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
that role's ``roles[].menu``, plus ``prototype.screens[].menu`` for screens that are not built, in
both directions (what the preview shows a persona is what its role gets).
"""

from __future__ import annotations

import importlib.util
import json
import re
import tempfile

from functools import lru_cache
from pathlib import Path


# What to do with a gap: spec_mark_ready's refusal, and the agent's brief when Commit finds one.
GUIDE = (
    "The user approves the preview as the app: whatever it shows is built, exactly, and nothing "
    "it doesn't show. "
    "Put each where it belongs in the YAML, with the prototype's own words: menu items, labels, "
    "groups and order → roles[].menu (a screen that is not built → its prototype.screens entry's "
    "`menu`). Each persona's menu in the prototype is its role's menu, exactly: the user approves "
    "what the preview shows. When the requirements give a role less than the prototype shows "
    "(one menu drawn for every persona), change the prototype so that persona's menu shows only "
    "its role's items (proto_patch the menu by persona), never the YAML to match a menu the role "
    "shouldn't have; page "
    "titles → pages[].title; columns → table.columns; status tabs and filter chips → "
    "table.quick_filters; where a row opens → table.row_click (its 360, `<view>#<tab>` for its "
    "parent's 360 on a tab, or drawer); 360 tabs → detail_views[].tabs, the prototype's tabs "
    "and no others; section and panel headings → a summary section's, sidebar block's or "
    "dashboard block's `title` (a field of that name is not a heading); buttons → "
    "header.actions.buttons, row_actions, add_button or a transition's label; field labels → "
    "the field's label, always in the preview's words (never renamed). If the YAML can't say it "
    "or can't lay it out as the preview does, set `rebuild: true` with a why on that screen's "
    "prototype.screens entry (the build ports the screen; a record screen of an uploaded page "
    "always is). Leave something out only when the user agreed to: list it under the entry's "
    "`not_built` as {text, why} and take it out of the preview too (proto_patch), so the "
    "preview never shows what won't be built."
)

CONTENT_KINDS = ("title", "heading", "column", "tab", "button", "label")
KIND_WORDS = {
    "title": "page title",
    "heading": "heading",
    "column": "column",
    "tab": "tab",
    "button": "button",
    "label": "field label",
    "extra_tab": "extra tab",
}
# gaps that are not a list of missing labels: (phrase, plural-free)
NOTE_KINDS = {
    "still_shown": "listed as not_built but the preview still shows",
    "needs_rebuild": "the preview's page layout",
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


def _titles(node, out: set, norm, key=None) -> set:
    """Titles a page or view shows: every ``title``, and each tab's ``label``."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "title" and isinstance(v, str):
                out.add(norm(v))
            elif k == "tabs" and isinstance(v, list):
                for t in v:
                    if isinstance(t, dict) and isinstance(t.get("label"), str):
                        out.add(norm(t["label"]))
                    _titles(t, out, norm)
            else:
                _titles(v, out, norm)
    elif isinstance(node, list):
        for v in node:
            _titles(v, out, norm)
    return out


def scope_titles(doc: dict, maps: str, norm) -> set:
    """The titles of the page or 360 a screen maps to (not its entities' field names): what a
    heading must match."""
    m = re.fullmatch(r"/(pages|detail_views)/@([A-Za-z0-9_]+)", str(maps or ""))
    if not m:
        return set()
    out: set = set()
    if m.group(1) == "pages":
        page = next(
            (p for p in _items(doc.get("pages")) if p.get("code") == m.group(2)), None
        )
        _titles(page or {}, out, norm)
    view = _view_of(doc, maps)
    if view:
        _titles(view, out, norm)
    return out


def covered(label: str, have: set, norm) -> bool:
    want = norm(label)
    if not want:
        return True
    padded = f" {want} "
    return any(want == h or padded in f" {h} " for h in have)


def _menu_labels(
    doc: dict, role: dict, screens: list, manifest: dict, norm, nav=None
) -> list:
    """``[(group, label)]`` a role's menu shows in the build, in order: roles[].menu, with the
    not-built screens' ``prototype.screens[].menu`` entries for this role placed as the shell
    places them (Shell.tsx ``withSoon``): at the end of their group, or as a new group after the
    group that comes before it in the prototype (``nav``)."""
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
    rank = {
        s.get("id"): i
        for i, s in enumerate(manifest.get("screens") or [])
        if isinstance(s, dict)
    }
    # the shell lists them in the prototype's order (spec_check.soon_items)
    for sc in sorted(screens, key=lambda s: rank.get(s.get("id"), len(rank))):
        menu = sc.get("menu")
        if not isinstance(menu, dict):
            continue
        roles = [norm(r) for r in menu.get("roles") or []]
        if roles and norm(role.get("name")) not in roles:
            continue
        _place(
            out,
            (
                menu.get("group"),
                menu.get("label") or proto_titles.get(sc.get("id")) or sc.get("id"),
            ),
            nav or [],
            norm,
        )
    return out


def _place(out: list, item: tuple, nav: list, norm) -> None:
    group = norm(item[0] or "")
    same = [i for i, (g, _) in enumerate(out) if norm(g or "") == group]
    if same:
        out.insert(same[-1] + 1, item)
        return
    order = []
    for g, _ in nav:
        if norm(g or "") not in order:
            order.append(norm(g or ""))
    if group in order:
        for before in reversed(order[: order.index(group)]):
            hit = [i for i, (g, _) in enumerate(out) if norm(g or "") == before]
            if hit:
                out.insert(hit[-1] + 1, item)
                return
    out.append(item)


def menu_gaps(doc: dict, manifest: dict, nav_by_persona: dict, norm) -> list[str]:
    """Each persona's menu in the prototype is its role's menu in the build: the same items, labels,
    groups and order, nothing more and nothing less. The user approves what the preview shows, so a
    role that sees less than the prototype's menu needs the prototype changed for that persona,
    not a lenient check."""
    roles = {norm(r.get("name")): r for r in _items(doc.get("roles"))}
    screens = _items((doc.get("prototype") or {}).get("screens"))
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
        have = _menu_labels(doc, role, screens, manifest, norm, nav)
        gaps += _role_menu_gaps(role.get("name"), nav, have, norm)
    return gaps


def _role_menu_gaps(name, nav: list, have: list, norm) -> list[str]:
    """One role's menu against its persona's in the prototype: missing, extra, groups, order."""
    index = {norm(label): (i, group) for i, (group, label) in enumerate(have)}
    shown = {norm(label) for _, label in nav}
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
    extra = [f"{label!r}" for _, label in have if norm(label) not in shown]
    gaps = []
    if absent:
        gaps.append(
            f"menu ({name}): the prototype shows this role {', '.join(absent)}; the YAML menu "
            "doesn't have them"
        )
    if extra:
        gaps.append(
            f"menu ({name}): the YAML menu has {', '.join(extra)}; the prototype doesn't show "
            "them to this role"
        )
    if wrong_group:
        gaps.append(f"menu ({name}): " + "; ".join(wrong_group))
    if order != sorted(order):
        gaps.append(
            f"menu ({name}): order differs from the prototype: "
            + ", ".join(label for _, label in nav)
        )
    return gaps


def _view_of(doc: dict, maps: str):
    """The detail view a ``maps`` target is (a 360, or a detail page's view), or None."""
    m = re.fullmatch(r"/(pages|detail_views)/@([A-Za-z0-9_]+)", str(maps or ""))
    if not m:
        return None
    kind, code = m.groups()
    if kind == "pages":
        page = next(
            (p for p in _items(doc.get("pages")) if p.get("code") == code), None
        )
        code = (page or {}).get("detail_view")
    return next(
        (v for v in _items(doc.get("detail_views")) if v.get("code") == code), None
    )


def row_gaps(doc: dict, capture: dict, norm) -> list[str]:
    """Where a list's rows go in the prototype (the capture's ``row_opens``) against ``table.row_click``:
    its own 360, its parent's 360 on a tab (``<view>#<tab>``), or a drawer."""
    entries = {
        s.get("id"): s for s in _items((doc.get("prototype") or {}).get("screens"))
    }
    pages = {p.get("code"): p for p in _items(doc.get("pages"))}
    entities = _entities(doc)
    views = _items(doc.get("detail_views"))
    gaps = []
    for sc in capture.get("screens") or []:
        goes = sc.get("row_opens")
        m = re.fullmatch(
            r"/pages/@([A-Za-z0-9_]+)",
            str((entries.get(sc.get("id")) or {}).get("maps") or ""),
        )
        page = pages.get(m.group(1)) if m else None
        if (
            not goes
            or not page
            or page.get("type") != "crud"
            or page.get("entity") not in entities
        ):
            continue
        ent = page["entity"]
        table = entities[ent].get("table") or {}
        own = next((v.get("code") for v in views if v.get("hero") == ent), None)
        have = table.get("row_click") or own or "drawer"
        where = f"{sc['id']} (/pages/@{page['code']})"
        if goes.get("overlay"):
            if have != "drawer":
                gaps.append(
                    f"{where}: a row opens a drawer in the prototype; table.row_click is {have!r} (set drawer)"
                )
            continue
        target = _view_of(doc, (entries.get(goes.get("screen")) or {}).get("maps"))
        if target is None:
            continue
        if target.get("hero") == ent:
            want = target.get("code")
        else:
            tabs = [
                t
                for t in target.get("tabs") or []
                if isinstance(t, dict) and t.get("entity") == ent
            ]
            hit = next(
                (t for t in tabs if norm(t.get("label")) == norm(goes.get("tab"))),
                tabs[0] if tabs else None,
            )
            if hit is None:
                gaps.append(
                    f"{where}: a row opens {target.get('code')} on its {goes.get('tab') or 'first'!r} tab in the "
                    f"prototype; {target.get('code')} has no related_table tab listing {ent} (add it)"
                )
                continue
            want = f"{target.get('code')}#{hit.get('code')}"
        if have != want:
            gaps.append(
                f"{where}: a row opens {goes.get('screen')}"
                + (
                    f" on its {goes['tab']!r} tab"
                    if goes.get("tab") and "#" in want
                    else ""
                )
                + f" in the prototype; set {ent}'s table.row_click: {want} (now {have!r})"
            )
    return gaps


def _tab_gaps(view, shown_tabs, skip, record, norm) -> dict:
    """A record page's tabs are the prototype's, exactly: none missing, none added. A record
    screen the prototype draws without tabs gets none."""
    if view is None or not (shown_tabs or record):
        return {}
    tabs = [
        t.get("label")
        for t in view.get("tabs") or []
        if isinstance(t, dict) and t.get("label")
    ]
    have = {norm(t) for t in tabs}
    shown = {norm(t) for t in shown_tabs}
    gaps = {}
    miss = [t for t in shown_tabs if norm(t) not in have]
    extra = [t for t in tabs if norm(t) not in shown and norm(t) not in skip]
    if miss:
        gaps["tab"] = miss
    if extra:
        gaps["extra_tab"] = extra
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
        # a top-bar button some screens hide (a "New" action) is still the shell's
        if len(sets) >= 4:
            counts: dict = {}
            for st in sets:
                for k, n in st:
                    if k == "button":
                        counts[n] = counts.get(n, 0) + 1
            chrome[persona] |= {
                ("button", n) for n, c in counts.items() if c * 2 > len(sets)
            }

    imported = manifest.get("source") == "imported"
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
        "menu": menu_gaps(doc, manifest, nav_by_persona, norm)
        + row_gaps(doc, capture, norm),
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
        still: list = []  # not_built, yet the preview shows it: the user would expect it built
        for persona, marks in per.items():
            for k in CONTENT_KINDS:
                for t in marks.get(k, []):
                    n = norm(t)
                    if (
                        (k == "title" and sid in records)
                        or (k, n) in chrome.get(persona, set())
                        or names & set(n.split())
                        or any(norm(x) == n for x in labels[k])
                    ):
                        continue
                    if n in skip:
                        if t not in still:
                            still.append(t)
                        continue
                    labels[k].append(t)
        m = re.fullmatch(r"/pages/@([A-Za-z0-9_]+)", entry["maps"])
        rebuilt = entry.get("rebuild") or (
            m and (pages.get(m.group(1)) or {}).get("type") == "custom"
        )
        view = _view_of(doc, entry["maps"])
        if rebuilt:
            out["rebuild"][sid] = {k: v for k, v in labels.items() if v}
            # the build ports the layout, but a record page's tabs are still the YAML's
            gaps = _tab_gaps(view, labels["tab"], skip, sid in records, norm)
            if still:
                gaps["still_shown"] = still
            if gaps:
                out["screens"].append({"id": sid, "maps": entry["maps"], "gaps": gaps})
            continue
        if imported and sid in records:
            # An uploaded page's record screen is its own layout (panels, trackers, cards); the
            # standard 360 can't draw it as the preview shows it, so the build ports it.
            gaps = {
                "needs_rebuild": [
                    "set `rebuild: true` with a why on this screen's entry"
                ]
            }
            if still:
                gaps["still_shown"] = still
            out["screens"].append({"id": sid, "maps": entry["maps"], "gaps": gaps})
            continue
        have = scope_labels(doc, entry["maps"], norm)
        titles = scope_titles(doc, entry["maps"], norm)
        gaps = {}
        for k, v in labels.items():
            if k == "tab" and view is not None:
                continue
            if k in ("title", "heading"):
                miss = [t for t in v if not covered(t, titles, norm)]
            else:
                miss = [t for t in v if not covered(t, have, norm)]
            if miss:
                gaps[k] = miss
        gaps.update(_tab_gaps(view, labels["tab"], skip, sid in records, norm))
        if still:
            gaps["still_shown"] = still
        if gaps:
            out["screens"].append({"id": sid, "maps": entry["maps"], "gaps": gaps})
    return out


def format_gaps(result: dict) -> str:
    lines = [f"- {g}" for g in result.get("menu") or []]
    for s in result.get("screens") or []:
        what = "; ".join(
            (
                f"{NOTE_KINDS[k]}: " + ", ".join(repr(t) for t in v)
                if k == "still_shown"
                else f"{NOTE_KINDS[k]}: {v[0]}"
                if k in NOTE_KINDS
                else f"{KIND_WORDS[k]}{'s' if len(v) > 1 else ''} "
                + ", ".join(repr(t) for t in v)
            )
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


def coverage_issues(doc: dict, parts: dict) -> list:
    """The coverage gaps as approval issues (``{level, path, message}``), for Commit. Empty when
    the YAML covers the prototype or it can't be rendered here."""
    design = (doc.get("app") or {}).get("design")
    try:
        bundle, _ = ensure_capture(
            parts, design=design if isinstance(design, dict) else None
        )
    except Exception:  # noqa: BLE001 - no browser here: spec_mark_ready said so already
        return []
    if bundle is None:
        return []
    result = coverage(doc, bundle)
    out = [
        {
            "level": "error",
            "path": "/roles" if g.startswith("menu") else "/modules",
            "message": g,
        }
        for g in result.get("menu") or []
    ]
    for s in result.get("screens") or []:
        line = format_gaps({"screens": [s]})[2:]
        out.append({"level": "error", "path": s["maps"], "message": line})
    return out
