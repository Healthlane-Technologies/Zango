"""What the person who made the app sees when a build ends: progress, never failures.

Testing and fixing are the platform's job. The build's checks are sorted here:

- ``harness``: our own test code broke (an exception inside zas_test, not an answer from the app).
  Never blocks the build, never goes to the agent's fix brief, never reaches the user.
- ``core``: the app cannot be used yet: the bring-up, the shell, signing in, a page that does not
  open, or a record that cannot be created. The user sees "Still building".
- ``polish``: anything else the app does not do as approved. The agent fixes it while the user
  already uses the app; the user sees only "finishing touches" on the screens concerned.

``user_status`` turns that into the chat card's words (references: AGENT_MODE_OPEN_PROTOTYPE_PLAN,
"Build status in chat"). The technical report keeps every check for the team.
"""

from __future__ import annotations

import json
import re

from pathlib import Path


# An exception raised by our own test code, as zas_test records it ("TypeError('…')").
_HARNESS = re.compile(
    r"^(TypeError|AttributeError|KeyError|IndexError|NameError|ValueError|UnboundLocalError|"
    r"ZeroDivisionError|RecursionError|ImportError|ModuleNotFoundError)\("
)
CORE_PREFIXES = ("ui.login",)


def _failures(layers: dict) -> list[dict]:
    out = []
    for name, layer in (layers or {}).items():
        fails = (
            layer.get("failures")
            if isinstance(layer, dict)
            else getattr(layer, "failures", [])
        )
        status = (
            layer.get("status")
            if isinstance(layer, dict)
            else getattr(layer, "status", "")
        )
        for f in fails or []:
            out.append({**f, "layer": name})
        if status == "fail" and not fails:
            out.append({"id": name, "layer": name, "title": name, "detail": ""})
    return out


def kind(f: dict) -> str:
    """harness | test | core | polish, for one failing check (see the module doc)."""
    fid, detail = str(f.get("id", "")), str(f.get("detail", "") or "")
    if _HARNESS.match(detail) and ".zas/test_scenarios.py" not in detail:
        return "harness"
    if (
        f.get("layer") == "scenarios"
        and ".zas/test_scenarios.py" in detail
        and not detail.startswith("AssertionError")
    ):
        return "test"  # the agent's own scenario script broke: the agent fixes it, the user never hears
    if f.get("layer") == "app_shell" or fid.startswith(CORE_PREFIXES):
        return "core"
    if fid.startswith("ui.page.") and (
        detail.startswith("no [data-zas=page]") or "shown as not implemented" in detail
    ):
        return "core"
    if fid.startswith("ui.flow.") and ".create." in fid:
        return "core"
    return "polish"


def sort_failures(layers: dict) -> dict:
    """{"harness", "test", "core", "polish": [...]} of the layers' failing checks."""
    out = {"harness": [], "test": [], "core": [], "polish": []}
    for f in _failures(layers):
        out[kind(f)].append(f)
    return out


def without_harness(layers: dict) -> dict:
    """The layers as the agent and the build's verdict see them: our own test bugs taken out."""
    out = {}
    for name, layer in layers.items():
        keep = [f for f in layer.failures if kind({**f, "layer": name}) != "harness"]
        if len(keep) == len(layer.failures):
            out[name] = layer
            continue
        clone = type(layer)(**{**layer.__dict__, "failures": keep})
        if not keep and clone.status == "fail":
            clone.status = "pass"
        out[name] = clone
    return out


def _area(M: dict, path: str) -> str | None:
    """The screen a spec path belongs to, by the title the user knows it by."""
    pages, ents, views = (
        M.get("pages") or {},
        M.get("entities") or {},
        M.get("detail_views") or {},
    )

    def list_title(ent):
        E = ents.get(ent) or {}
        page = pages.get(E.get("list_page") or "") or next(
            (
                p
                for p in pages.values()
                if p.get("entity") == ent and p.get("type") == "crud"
            ),
            None,
        )
        return (page or {}).get("title") or E.get("plural") or E.get("name")

    parts = str(path or "").split(".")
    if len(parts) > 1 and parts[0] == "pages":
        return (pages.get(parts[1]) or {}).get("title")
    if len(parts) > 1 and parts[0] == "entities":
        return list_title(parts[1])
    if len(parts) > 1 and parts[0] == "detail_views":
        return list_title((views.get(parts[1]) or {}).get("hero"))
    if parts[0] == "roles":
        return "the menu"
    return None


def _steps(M: dict, results: list[dict]) -> list[dict]:
    """Per role, the steps it was seen doing in the browser: [{role, steps: [label]}]."""
    ents = M.get("entities") or {}
    by_role: dict = {}
    for r in results:
        rid = str(r.get("id", ""))
        if (
            not rid.startswith("ui.flow.")
            or r.get("status") != "pass"
            or not r.get("role")
        ):
            continue
        parts = rid.split(".")
        title = str(r.get("title", ""))
        if len(parts) > 3 and parts[3] == "create":
            E = ents.get(parts[2]) or {}
            label = (E.get("table") or {}).get(
                "add_button"
            ) or f"Add {str(E.get('name', parts[2])).lower()}"
        else:
            m = re.match(
                r"([^:]+):\s*(.+?)(?: from the (?:360|list page|.+? tab))?$", title
            )
            label = m.group(2) if m else title
            if m and len(label.split()) == 1:  # "Upload" → "Upload evidence item"
                label = f"{label} {m.group(1).strip().lower()}"
        steps = by_role.setdefault(r["role"], [])
        if label not in steps:
            steps.append(label)
    order = list(M.get("roles") or {})
    return [
        {"role": role, "steps": by_role[role]} for role in order if by_role.get(role)
    ] + [{"role": role, "steps": s} for role, s in by_role.items() if role not in order]


def _names(items: list[str], most=3) -> str:
    items = list(dict.fromkeys(i for i in items if i))
    if len(items) <= most:
        return (
            ", ".join(items[:-1])
            + (" and " if len(items) > 1 else "")
            + (items[-1] if items else "")
        )
    return ", ".join(items[:most]) + f" and {len(items) - most} more"


def user_status(
    workspace: str, layers: dict, bring_up_ok: bool, *, active: bool, app_url: str = ""
) -> dict:
    """The chat card: {state, headline, body, finishing, roles, tried, app_url, active}.

    state: "building" (a core step fails), "finishing" (only polish left), "ready".
    ``active``: fix rounds are still going (the finishing line says "about to"; else "our team").
    """
    zas = Path(workspace) / ".zas"
    try:
        M = json.loads((zas / "spec.resolved.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        M = {}
    try:
        res = json.loads((zas / "test_results.json").read_text(encoding="utf-8"))
        results = res.get("results") if isinstance(res, dict) else res
    except (OSError, ValueError):
        results = []
    results = results or []
    app = (M.get("app") or {}).get("name") or "Your"
    sorted_ = sort_failures(layers)
    areas = [
        a
        for a in (
            _area(M, f.get("spec_path") or f.get("id")) for f in sorted_["polish"]
        )
        if a
    ]
    flows = [
        r
        for r in results
        if str(r.get("id", "")).startswith("ui.flow.")
        and r.get("status") in ("pass", "fail")
    ]
    screens = {
        str(r.get("id", "")).split(".")[3]
        for r in results
        if str(r.get("id", "")).startswith("design.parity.proto.")
    }
    roles = {r.get("role") for r in flows if r.get("role")}
    base = {
        "app_url": app_url,
        "active": active,
        "roles": _steps(M, results),
        "tried": {"steps": len(flows), "roles": len(roles), "screens": len(screens)},
    }
    if not bring_up_ok or sorted_["core"]:
        return {
            **base,
            "state": "building",
            "headline": "We're still building your app",
            "body": "The screens are in place; we're finishing the last steps before you can sign in. "
            "We'll message you here as soon as it's ready.",
            "finishing": None,
            "roles": [],
        }
    if sorted_["polish"]:
        where = _names(areas) or "a few screens"
        return {
            **base,
            "state": "finishing",
            "headline": f"Your {app} app is ready",
            "body": "Every role can sign in and use the app. We're still putting the finishing touches on "
            "a few screens from your preview; you can use the app meanwhile.",
            "finishing": (
                f"Finishing touches on {where}"
                if active
                else f"Our team is finishing the last touches on {where}"
            ),
        }
    return {
        **base,
        "state": "ready",
        "headline": f"Your {app} app is ready",
        "body": "Everything you approved is built, matches your preview, and works for every role.",
        "finishing": None,
    }
