"""Open mode: does the spec cover everything the approved prototype shows? (spec_mark_ready)

The build follows the YAML, so whatever the prototype shows and the YAML leaves out is lost: a
menu item, a column, a status tab, a 360 tab, a section, a button. Before the user approves, the
prototype is rendered for every persona (the probe worker's ``--open`` capture, cached by parts
hash) and each screen's labels (skill ``scripts/proto_landmarks.py``) are matched against the part
of the YAML that screen maps to.

A label is covered when the YAML says it there, or the screen's ``prototype.screens`` entry lists
it under ``not_built`` with a why (the user sees those). A rebuilt screen (custom page, or
``rebuild: true``) is ported from the prototype itself, so its labels go to the build instead of
blocking. The menu is checked per persona: the prototype's items, labels, groups and order against
that role's ``roles[].menu``, plus ``prototype.screens[].menu`` for screens that are not built.
"""

from __future__ import annotations

import importlib.util
import json
import re
import tempfile

from functools import lru_cache
from pathlib import Path


CONTENT_KINDS = ("title", "heading", "column", "tab", "button", "label")
KIND_WORDS = {
    "title": "page title",
    "heading": "heading",
    "column": "column",
    "tab": "tab",
    "button": "button",
    "label": "field label",
}


@lru_cache(maxsize=1)
def landmarks_module():
    """skill ``scripts/proto_landmarks.py`` (shared with spec_check), loaded by path."""
    from zango.apps.shared.app_templates.services.generic import studio_plugin_dir

    path = (
        Path(studio_plugin_dir())
        / "skills"
        / "zango-app-studio"
        / "scripts"
        / "proto_landmarks.py"
    )
    spec = importlib.util.spec_from_file_location("zas_proto_landmarks", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _items(x) -> list:
    """A spec list, or a mapping of code → object, as a list of objects."""
    if isinstance(x, dict):
        return [
            {"code": k, **v} if isinstance(v, dict) else {"code": k}
            for k, v in x.items()
        ]
    return [v for v in (x or []) if isinstance(v, dict)]


def _strings(node, out: set, norm) -> set:
    """Every string in ``node``, and every key humanised (``amount_requested`` → amount requested)."""
    if isinstance(node, str):
        out.add(norm(node))
    elif isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str) and re.fullmatch(r"[a-z][a-z0-9_]*", k):
                out.add(norm(k.replace("_", " ")))
            _strings(v, out, norm)
    elif isinstance(node, list):
        for v in node:
            _strings(v, out, norm)
    return out


def _entities(doc: dict) -> dict:
    out = {}
    for m in _items(doc.get("modules")):
        for e in _items(m.get("entities")):
            if e.get("code"):
                out[e["code"]] = e
    return out


def _referenced(node, out: set) -> set:
    """Entity codes a page or view points at (``entity:``, ``hero:``)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("entity", "hero") and isinstance(v, str):
                out.add(v)
            else:
                _referenced(v, out)
    elif isinstance(node, list):
        for v in node:
            _referenced(v, out)
    return out


def scope_labels(doc: dict, maps: str, norm) -> set:
    """The YAML a screen maps to (its page or 360 view, and the entities they show), as labels."""
    m = re.fullmatch(r"/(pages|detail_views)/@([A-Za-z0-9_]+)", str(maps or ""))
    if not m:
        return set()
    kind, code = m.groups()
    nodes = []
    if kind == "pages":
        page = next(
            (p for p in _items(doc.get("pages")) if p.get("code") == code), None
        )
        if page:
            nodes.append(page)
            if page.get("detail_view"):
                kind, code = "detail_views", page["detail_view"]
    if kind == "detail_views":
        nodes += [v for v in _items(doc.get("detail_views")) if v.get("code") == code]
    entities = _entities(doc)
    for code in sorted(
        set().union(*(_referenced(n, set()) for n in nodes)) if nodes else ()
    ):
        if code in entities:
            nodes.append(entities[code])
    out: set = set()
    for n in nodes:
        _strings(n, out, norm)
    return out


def covered(label: str, have: set, norm) -> bool:
    want = norm(label)
    if not want:
        return True
    padded = f" {want} "
    return any(want == h or padded in f" {h} " for h in have)


def _menu_labels(doc: dict, role: dict, screens: list, manifest: dict, norm) -> list:
    """``[(group, label)]`` a role's menu shows in the build, in order: roles[].menu, then the
    not-built screens' ``prototype.screens[].menu`` entries for this role."""
    titles = {p.get("code"): p.get("title") for p in _items(doc.get("pages"))}
    out = []
    for it in role.get("menu") or []:
        if not isinstance(it, dict):
            continue
        if it.get("items"):
            for sub in it["items"]:
                if isinstance(sub, dict):
                    out.append(
                        (
                            it.get("group"),
                            sub.get("label") or titles.get(sub.get("page")) or "",
                        )
                    )
        elif it.get("page") or it.get("label"):
            out.append((None, it.get("label") or titles.get(it.get("page")) or ""))
    proto_titles = {
        s.get("id"): s.get("title")
        for s in manifest.get("screens") or []
        if isinstance(s, dict)
    }
    for sc in screens:
        menu = sc.get("menu")
        if not isinstance(menu, dict):
            continue
        roles = [norm(r) for r in menu.get("roles") or []]
        if roles and norm(role.get("name")) not in roles:
            continue
        out.append(
            (
                menu.get("group"),
                menu.get("label") or proto_titles.get(sc.get("id")) or sc.get("id"),
            )
        )
    return out


def menu_gaps(doc: dict, manifest: dict, nav_by_persona: dict, norm) -> list[str]:
    """Each prototype menu item is in the YAML's menus, with its label, group and order.

    When every persona sees its own menu, each role is checked against its persona's. When they all
    see the same one, the prototype doesn't say who sees what: every item must be in some role's
    menu, and the role with the fullest menu keeps the prototype's groups and order."""
    roles = {norm(r.get("name")): r for r in _items(doc.get("roles"))}
    screens = _items((doc.get("prototype") or {}).get("screens"))
    navs = {
        tuple((norm(g or ""), norm(t)) for g, t in nav)
        for nav in nav_by_persona.values()
    }
    if len(navs) == 1 and len(nav_by_persona) > 1:
        nav = next(iter(nav_by_persona.values()))
        menus = [
            (r, _menu_labels(doc, r, screens, manifest, norm)) for r in roles.values()
        ]
        if not menus:
            return []
        anywhere = {norm(label) for _, have in menus for _, label in have}
        missing = [
            f"{label!r}" + (f" (group {group!r})" if group else "")
            for group, label in nav
            if norm(label) not in anywhere
        ]
        gaps = ["menu: in no role's menu: " + ", ".join(missing)] if missing else []
        role, have = max(
            menus,
            key=lambda m: len({norm(t) for _, t in m[1]} & {norm(t) for _, t in nav}),
        )
        return gaps + _role_menu_gaps(role.get("name"), nav, have, norm, missing=False)
    gaps = []
    for persona, nav in nav_by_persona.items():
        role_name = (manifest.get("roles") or {}).get(persona) or persona
        role = roles.get(norm(role_name))
        if role is None:
            gaps.append(
                f"menu: persona {persona!r} is role {role_name!r} in the prototype, and the YAML "
                "has no role by that name"
            )
            continue
        have = _menu_labels(doc, role, screens, manifest, norm)
        gaps += _role_menu_gaps(role.get("name"), nav, have, norm)
    return gaps


def _role_menu_gaps(name, nav: list, have: list, norm, missing=True) -> list[str]:
    """One role's menu against the prototype's: missing items, groups, order."""
    index = {norm(label): (i, group) for i, (group, label) in enumerate(have)}
    absent, wrong_group, order = [], [], []
    for group, label in nav:
        hit = index.get(norm(label))
        if hit is None:
            absent.append(f"{label!r}" + (f" (group {group!r})" if group else ""))
            continue
        order.append(hit[0])
        if norm(group or "") != norm(hit[1] or ""):
            wrong_group.append(
                f"{label!r} is under {group or 'no group'!r} in the prototype, "
                f"{hit[1] or 'no group'!r} in the YAML"
            )
    gaps = []
    if absent and missing:
        gaps.append(f"menu ({name}): missing " + ", ".join(absent))
    if wrong_group:
        gaps.append(f"menu ({name}): " + "; ".join(wrong_group))
    if order != sorted(order):
        gaps.append(
            f"menu ({name}): order differs from the prototype: "
            + ", ".join(label for _, label in nav)
        )
    return gaps


def coverage(doc: dict, bundle_dir) -> dict:
    """``{"menu": [gap], "screens": [{id, maps, gaps: {kind: [label]}}], "rebuild": {id: {kind: [label]}}}``
    for the capture in ``bundle_dir`` (``write_prototype_bundle``'s output)."""
    lm = landmarks_module()
    norm = lm.norm
    bundle = Path(bundle_dir)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    capture = json.loads((bundle / "capture.json").read_text(encoding="utf-8"))
    personas = manifest.get("personas") or {}
    names = {
        w
        for p in personas.values()
        if isinstance(p, dict)
        for w in norm(p.get("name")).split()
        if len(w) > 2
    }
    entries = {
        s.get("id"): s for s in _items((doc.get("prototype") or {}).get("screens"))
    }
    pages = {p.get("code"): p for p in _items(doc.get("pages"))}

    # every persona's labels on every screen it opens
    seen: dict = {}  # screen id → persona → landmarks
    for sc in capture.get("screens") or []:
        for r in sc.get("roles") or []:
            dom = next((f for f in r.get("files") or [] if f.startswith("dom.")), None)
            src = r.get("same_as") or r.get("role")
            if not dom and r.get("same_as"):
                dom = f"dom.{r['same_as']}.html"
            path = bundle / "screens" / sc["id"] / (dom or f"dom.{src}.html")
            if path.is_file():
                seen.setdefault(sc["id"], {})[r.get("role")] = lm.landmarks(
                    path.read_text(encoding="utf-8")
                )

    nav_by_persona: dict = {}
    for per in seen.values():
        for persona, marks in per.items():
            if marks.get("menu") and persona not in nav_by_persona:
                nav_by_persona[persona] = marks["menu"]

    # chrome: what a persona sees on every screen (top bar, user card) belongs to the shell
    chrome: dict = {}
    for persona in nav_by_persona:
        sets = [
            {(k, norm(t)) for k in CONTENT_KINDS for t in per[persona].get(k, [])}
            for per in seen.values()
            if persona in per
        ]
        chrome[persona] = set.intersection(*sets) if len(sets) > 1 else set()

    records = {
        s.get("id")
        for s in manifest.get("screens") or []
        if isinstance(s, dict) and s.get("record")
    }
    # a screen that renders exactly like an earlier one (a form opened over a list, say) adds nothing
    sig = lambda per: json.dumps(  # noqa: E731
        sorted((p, {k: per[p].get(k) for k in CONTENT_KINDS}) for p in per),
        sort_keys=True,
    )
    firsts: dict = {}
    out = {
        "menu": menu_gaps(doc, manifest, nav_by_persona, norm),
        "screens": [],
        "rebuild": {},
    }
    for sid, per in seen.items():
        entry = entries.get(sid) or {}
        if entry.get("only") == "prototype" or not entry.get("maps"):
            continue
        if firsts.setdefault(sig(per), sid) != sid:
            continue
        skip = {
            norm(x.get("text") if isinstance(x, dict) else x)
            for x in entry.get("not_built") or []
        }
        labels: dict = {k: [] for k in CONTENT_KINDS}
        for persona, marks in per.items():
            for k in CONTENT_KINDS:
                for t in marks.get(k, []):
                    n = norm(t)
                    if (
                        (k == "title" and sid in records)
                        or (k, n) in chrome.get(persona, set())
                        or n in skip
                        or names & set(n.split())
                        or any(norm(x) == n for x in labels[k])
                    ):
                        continue
                    labels[k].append(t)
        m = re.fullmatch(r"/pages/@([A-Za-z0-9_]+)", entry["maps"])
        rebuilt = entry.get("rebuild") or (
            m and (pages.get(m.group(1)) or {}).get("type") == "custom"
        )
        if rebuilt:
            out["rebuild"][sid] = {k: v for k, v in labels.items() if v}
            continue
        have = scope_labels(doc, entry["maps"], norm)
        gaps = {
            k: [t for t in v if not covered(t, have, norm)] for k, v in labels.items()
        }
        gaps = {k: v for k, v in gaps.items() if v}
        if gaps:
            out["screens"].append({"id": sid, "maps": entry["maps"], "gaps": gaps})
    return out


def format_gaps(result: dict) -> str:
    lines = [f"- {g}" for g in result.get("menu") or []]
    for s in result.get("screens") or []:
        what = "; ".join(
            f"{KIND_WORDS[k]}{'s' if len(v) > 1 else ''} "
            + ", ".join(repr(t) for t in v)
            for k, v in s["gaps"].items()
        )
        lines.append(f"- {s['id']} ({s['maps']}): {what}")
    return "\n".join(lines)


def capture_dir(parts: dict) -> Path:
    from .prototype import parts_hash

    return Path(tempfile.gettempdir()) / "zas-proto-coverage" / parts_hash(parts)


def ensure_capture(parts: dict, design=None) -> tuple[Path | None, str]:
    """The prototype rendered for every persona (cached by parts hash): ``(dir, "")``, or
    ``(None, why)`` when it can't be rendered here."""
    from .approval_bundle import write_prototype_bundle

    out = capture_dir(parts)
    cap = out / "capture.json"
    if cap.is_file():
        probe = json.loads(cap.read_text(encoding="utf-8")).get("probe")
        if probe == "ok":
            return out, ""
    capture = write_prototype_bundle(parts, out, design=design)
    if capture.get("probe") != "ok":
        return None, str(capture.get("probe"))
    return out, ""
