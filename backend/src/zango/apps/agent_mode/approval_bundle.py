"""The approval bundle: what the user approved in the preview, for the build agent (spec-to-build F2).

The build gets the YAML; the runtime draws lists, forms, workflows and 360 pages from it. Custom
screens (custom pages, 360 tabs and panels) are written by the build agent, so for each one the
bundle keeps what the user actually saw:

    .zas/bundle/
      index.md                     what is here, screen by screen (read this first)
      manifest.json                the same as data
      screens/<screen>/
        sketch.js                  the preview sketch: port it onto zas/ui.tsx, hand-drawn markup included
        contract.json              text, data, interactions, states, acceptance, refs
        view.<role>.json           the kit tree the sketch drew for that role, and its summary
        shot.<role>.png            the screen as that role saw it (one per distinct structure)
        in_page.<role>.png         a tab or panel in its 360 page
      screens/pages.<page>.views.<i>/   a list page with declared views, in view <i> (shell included)
        shot.<role>.png, layout.json  the screen, and where its switcher sits
      screens/shell/               the app shell (sidebar, top bar) on a role's landing page
        shot.<role>.png, layout.json  the screen, and what the shell shows

The standard screens (list pages with views, the shell) are drawn by the runtime, which the build
agent arranges at defined points (the switcher's place, the shell's logo, user card and top bar)
but does not edit: their shots show it the layout to arrange.

Roles whose screen has the same kit tree share one view and one screenshot, so a screenshot
means a layout the build must actually produce. Values are demo data: the build matches the
structure, never the numbers. Without Playwright the bundle still has the sketches and
contracts; index.md says the screenshots are missing.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import re

from datetime import datetime, timezone
from pathlib import Path

import yaml


logger = logging.getLogger(__name__)

MAX_VARIANTS = 3
CONTRACT_KEYS = (
    "title",
    "label",
    "text",
    "data",
    "interactions",
    "states",
    "acceptance",
    "refs",
    "component",
    "roles",
    "show_when",
)


def kit_tree_js() -> str:
    """The extractor shared with the build's parity check (skill scripts/zas_test/kit_tree.js)."""
    from zango.apps.shared.app_templates.services.generic import studio_plugin_dir

    return (
        Path(studio_plugin_dir())
        / "skills"
        / "zango-app-studio"
        / "scripts"
        / "zas_test"
        / "kit_tree.js"
    ).read_text()


def screen_folder(path: str) -> str:
    """``/detail_views/@vendor_360/sidebar/2`` → ``detail_views.vendor_360.sidebar.2`` (the hole's spec path)."""
    return ".".join(seg.lstrip("@") for seg in path.strip("/").split("/"))


def _slug(role: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", role.lower()).strip("_") or "role"


def _outline(tree: list, depth: int = 0) -> list:
    lines = []
    for node in tree or []:
        if node["kit"] == "markup":
            text = node.get("text") or ""
            line = (
                "  " * depth
                + f'- hand-drawn block "{text[:50]}{"…" if len(text) > 50 else ""}"'
            )
        else:
            line = "  " * depth + f"- {node['kit']}"
            if node.get("title"):
                line += f' "{node["title"]}"'
            if node.get("items"):
                line += ": " + ", ".join(node["items"])
        if node.get("look"):
            line += f" [look: {', '.join(node['look'])}]"
        lines.append(line)
        lines += _outline(node.get("children") or [], depth + 1)
    return lines


def _has_kit_blocks(tree: list) -> bool:
    """Whether the tree has any kit block; hand-drawn markup alone does not count."""
    return any(
        n.get("kit") != "markup" or _has_kit_blocks(n.get("children") or [])
        for n in tree or []
    )


def write_bundle(
    spec_text: str, out_dir, *, probe=None, template_version: str = ""
) -> dict:
    """Write the bundle for ``spec_text`` into ``out_dir``; returns the manifest.

    ``probe``: a PreviewProbe (preview_probe.probe_for); None writes sketches and contracts only.
    """
    from .preview_probe import ProbeError, custom_screens, is_sketched

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = yaml.safe_load(spec_text or "") or {}
    screens = custom_screens(doc) if isinstance(doc, dict) else {}
    layouts = layout_screens(doc)
    manifest = {
        "version": 1,
        "spec_sha256": hashlib.sha256((spec_text or "").encode()).hexdigest(),
        "template_version": template_version,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "probe": "ok"
        if probe is not None
        else "unavailable: the preview could not run here (no Playwright)",
        "screens": [],
    }
    kit_js = kit_tree_js() if probe is not None and screens else ""
    if probe is not None and (screens or layouts):
        try:
            listed = probe.sketches(spec_text)
            if listed.get("parse_error"):
                manifest["probe"] = (
                    f"unavailable: the preview could not read the spec ({listed['parse_error']})"
                )
                probe = None
        except ProbeError as exc:
            manifest["probe"] = f"unavailable: {exc}"
            probe = None

    for path, node in screens.items():
        node = node if isinstance(node, dict) else {}
        folder = screen_folder(path)
        sdir = out / "screens" / folder
        sdir.mkdir(parents=True, exist_ok=True)
        entry = {
            "path": path,
            "folder": f"screens/{folder}",
            "kind": None,
            "title": node.get("title") or node.get("label"),
            "sketched": is_sketched(node),
            "variants": [],
            "in_page": None,
        }
        (sdir / "contract.json").write_text(
            json.dumps(
                {k: node[k] for k in CONTRACT_KEYS if k in node}, indent=2, default=str
            )
        )
        if entry["sketched"]:
            sketch = str(node["preview"]).rstrip() + "\n"
            (sdir / "sketch.js").write_text(sketch)
            entry["sketch"] = f"screens/{folder}/sketch.js"
            # raw HTML beside the kit calls: the kit outline cannot show it, only the screenshot does
            entry["markup"] = has_markup(sketch)
        if probe is not None and entry["sketched"]:
            try:
                res = probe.capture(spec_text, path, kit_js, MAX_VARIANTS)
            except ProbeError as exc:
                entry["error"] = str(exc)
                res = {}
            if res.get("error"):
                entry["error"] = res["error"]
            entry["kind"] = res.get("kind")
            for v in res.get("variants") or []:
                role = _slug(v["roles"][0])
                run = v.get("run") or {}
                view = {
                    "roles": v["roles"],
                    "record": v.get("record"),
                    "tree": v.get("tree") or [],
                    "hand_written": not _has_kit_blocks(v.get("tree")),
                    "draws": run.get("draws") or [],
                    "excerpt": run.get("excerpt"),
                    "warnings": run.get("warnings") or [],
                }
                (sdir / f"view.{role}.json").write_text(json.dumps(view, indent=2))
                item = {
                    "roles": v["roles"],
                    "view": f"screens/{folder}/view.{role}.json",
                    "tree": view["tree"],
                    "hand_written": view["hand_written"],
                    "shot": None,
                    "record": v.get("record"),
                }
                if v.get("png"):
                    (sdir / f"shot.{role}.png").write_bytes(base64.b64decode(v["png"]))
                    item["shot"] = f"screens/{folder}/shot.{role}.png"
                entry["variants"].append(item)
            if res.get("in_page") and entry["variants"]:
                role = _slug(entry["variants"][0]["roles"][0])
                (sdir / f"in_page.{role}.png").write_bytes(
                    base64.b64decode(res["in_page"])
                )
                entry["in_page"] = f"screens/{folder}/in_page.{role}.png"
        manifest["screens"].append(entry)

    for item in layouts:
        manifest["screens"].append(_layout_entry(out, item, spec_text, probe))

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "index.md").write_text(index_md(manifest))
    return manifest


def layout_screens(doc) -> list:
    """The standard screens the build arranges: every crud page that declares two or more views
    (one entry per view, so the switcher and each view are shot), then the app shell."""
    if not isinstance(doc, dict):
        return []
    out = []
    for page in doc.get("pages") or []:
        if (
            not isinstance(page, dict)
            or page.get("type") != "crud"
            or not page.get("code")
        ):
            continue
        views = [v for v in page.get("views") or [] if isinstance(v, dict)]
        if len(views) < 2:
            continue
        for i, v in enumerate(views):
            out.append(
                {
                    "kind": "view",
                    "page": page["code"],
                    "view": i,
                    "view_type": v.get("type") or "table",
                    "title": f"{page.get('title') or page['code']} · {v.get('label') or (v.get('type') or 'table').title()}",
                }
            )
    if doc.get("pages"):
        out.append({"kind": "shell", "page": None, "view": 0, "title": "App shell"})
    return out


def _layout_entry(out: Path, item: dict, spec_text: str, probe) -> dict:
    """One standard screen: its folder, layout.json and screenshot (when the preview can shoot)."""
    from .preview_probe import ProbeError

    if item["kind"] == "view":
        path = f"/pages/@{item['page']}/views/{item['view']}"
        folder = f"pages.{item['page']}.views.{item['view']}"
    else:
        path, folder = "/shell", "shell"
    sdir = out / "screens" / folder
    sdir.mkdir(parents=True, exist_ok=True)
    entry = {
        "path": path,
        "folder": f"screens/{folder}",
        "kind": item["kind"],
        "title": item["title"],
        "page": item["page"],
        "view_type": item.get("view_type"),
        "sketched": False,
        "variants": [],
        "in_page": None,
        "layout": None,
    }
    if probe is None or not hasattr(probe, "capture_layout"):
        return entry
    try:
        res = probe.capture_layout(
            spec_text, item["kind"], page=item["page"], view=item["view"]
        )
    except ProbeError as exc:
        entry["error"] = str(exc)
        return entry
    if res.get("error") or res.get("parse_error"):
        entry["error"] = res.get("error") or res.get("parse_error")
        return entry
    role = res.get("role") or ""
    entry["layout"] = res.get("layout") or {}
    if item["kind"] == "shell":
        entry["page"] = res.get("page")
    (sdir / "layout.json").write_text(
        json.dumps({"role": role, "page": res.get("page"), **entry["layout"]}, indent=2)
    )
    variant = {
        "roles": [role],
        "tree": [],
        "hand_written": False,
        "shot": None,
        "record": None,
    }
    if res.get("png"):
        (sdir / f"shot.{_slug(role)}.png").write_bytes(base64.b64decode(res["png"]))
        variant["shot"] = f"screens/{folder}/shot.{_slug(role)}.png"
    entry["variants"].append(variant)
    return entry


MARKUP = re.compile(
    r"<(?:div|span|b|i|svg|section|p|h\d|ul|li|table|img)\b[^>]*>", re.I
)


def has_markup(sketch: str) -> bool:
    """Whether a sketch draws raw HTML (its own markup and styles), not only ``ui.*`` kit calls."""
    return bool(MARKUP.search(sketch or ""))


def index_md(manifest: dict) -> str:
    """The bundle as the build agent reads it: one section per custom screen, outline first."""
    lines = [
        "# Approval bundle",
        "",
        "What the user approved in the App Studio preview, for each custom screen. The build has to",
        "look like it. **Before you write a screen's slot, Read its screenshot(s) and its `sketch.js`**:",
        "the screenshot is the look to reproduce, the sketch is how it was drawn. Port `ui.*` calls onto",
        "the zas kit and hand-drawn markup with the sketch's own styles (references/custom-code.md,",
        '"Porting a sketch"). The outline below is what the parity check compares: the blocks, their',
        "labels and each block's `[look: …]` (gradient, filled, chart, avatar, accent), which the built",
        "block must have too. Screenshots show demo data: match the look, never the numbers.",
        "",
    ]
    if manifest.get("probe") != "ok":
        lines += [
            f"> No screenshots or kit outlines: {manifest.get('probe')}. Build from the sketch and the contract.",
            "",
        ]
    custom = [s for s in manifest.get("screens") or [] if s.get("kind") not in STANDARD]
    standard = [s for s in manifest.get("screens") or [] if s.get("kind") in STANDARD]
    if not custom:
        lines.append("No custom screens in this spec.")
    for s in custom:
        lines.append(
            f"## `{s['path']}`" + (f" — {s['title']}" if s.get("title") else "")
        )
        lines.append("")
        lines.append(
            f"- Folder: `{s['folder']}/` (contract.json"
            + (", sketch.js" if s.get("sketched") else "")
            + ")"
        )
        if not s.get("sketched"):
            lines.append("- No sketch: build from the contract's text.")
        elif s.get("markup") and not all(
            v.get("hand_written") for v in s.get("variants") or [{}]
        ):
            lines.append(
                "- Has hand-drawn parts (raw HTML and inline styles beside the kit calls): port them "
                "from `sketch.js` with its styles, checked against the screenshot"
            )
        if s.get("error"):
            lines.append(f"- Could not capture: {s['error']}")
        for v in s.get("variants") or []:
            who = ", ".join(v["roles"])
            rec = (
                f" on {v['record']['entity']} #{v['record']['id']}"
                if v.get("record")
                else ""
            )
            lines.append(
                f"- As {who}{rec}: "
                + (f"`{v['shot']}`" if v.get("shot") else "no screenshot")
            )
            if v.get("hand_written"):
                lines.append(
                    "  - hand-written markup (no kit blocks): port it from `sketch.js` with its styles, checked against the screenshot"
                )
            else:
                lines += ["  " + ln for ln in _outline(v["tree"])]
        if s.get("in_page"):
            lines.append(f"- In its 360 page: `{s['in_page']}`")
        lines.append("")
    if standard:
        lines += standard_md(standard)
    return "\n".join(lines)


STANDARD = ("view", "shell")


def standard_md(screens: list) -> list:
    """The standard screens' section of index.md: what to arrange, and with which lever."""
    lines = [
        "# Standard screens: arrange them like the preview",
        "",
        "The runtime draws these (list pages, the switcher, the shell). Never edit `src/zas/` or",
        "`ViewsPage.tsx`; arrange them with the levers below, then compare with the screenshot",
        '(`references/views.md` "Matching the approved page", `references/custom-code.md` "The app shell").',
        "Each shot is the whole app at 1440px with demo data: match the layout, never the values.",
        "",
    ]
    for s in screens:
        lay = s.get("layout") or {}
        lines.append(f"## `{s['path']}` — {s.get('title') or ''}".rstrip(" —"))
        lines.append("")
        for v in s.get("variants") or []:
            who = ", ".join(r for r in v["roles"] if r)
            lines.append(
                f"- As {who or 'the first role'}: "
                + (f"`{v['shot']}`" if v.get("shot") else "no screenshot")
            )
        if s.get("error"):
            lines.append(f"- Could not capture: {s['error']}")
        if s["kind"] == "view":
            place = lay.get("switcher")
            if place == "toolbar":
                lines.append(
                    f'- Switcher in the toolbar, before Export: `makeViewsPage("{s["page"]}", {{ … }}, '
                    '{ switcher: "toolbar" })`; a custom view renders `props.switcher` in its own '
                    '`zas-tb` toolbar row, at the right, before Export.'
                )
            elif place == "header":
                lines.append(
                    "- Switcher above the page (the default `makeViewsPage` placement)."
                )
            if s.get("view_type") and s["view_type"] != "table":
                lines.append(
                    f"- The {s['view_type']} view: `frontend/src/custom/views/{s['page']}_{s['view_type']}.tsx`"
                    " when this runtime has no component for it (`.zas/views.md`)."
                )
        else:
            sh = lay.get("shell") or {}
            if sh.get("brand"):
                role_note = (
                    f', then the role "{sh["brand_role"]}"'
                    if sh.get("brand_role")
                    else ""
                )
                lines.append(
                    f'- Sidebar header: the app\'s initials avatar and "{sh["brand"]}"{role_note}: '
                    '`navbarConfig.customLogo`, root marked `data-zas="shell-brand"`.'
                )
            if sh.get("user_in_sidebar"):
                lines.append(
                    "- User card at the bottom of the sidebar (avatar, name, role): "
                    '`navbarConfig.customBottomContent`, root `data-zas="shell-user"`; '
                    "`topbarConfig.showProfile: false` so it is not shown twice."
                )
            if sh.get("topbar"):
                n = sh.get("topbar_actions") or 0
                lines.append(
                    "- Top bar with the page title (breadcrumb on a 360 page)"
                    + (f" and {n} icon button(s) at the right" if n else "")
                    + ': `topbarConfig.customLeftContent` / `customRightContent`, root `data-zas="shell-top"`.'
                )
            lines.append(
                "- Write these in `frontend/src/custom/shell/` from the zas kit and pass them in `src/App.tsx`."
            )
        lines.append("")
    return lines


# --- open mode (Free design): the approved prototype ---------------------------------------------
# The build follows the prototype, so it gets what each screen looks like for each role: the
# rendered markup (scripts removed) and a screenshot, captured in the probe worker. It ports from
# these, never from the prototype's own code (an imported page is one big script).

PROTOTYPE_CAPTURE_TIMEOUT = 600
_URL_RE = re.compile(
    r"https://(?:cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net|unpkg\.com)/[^\s\"'<>)]+"
)


def prototype_libraries(parts: dict) -> list:
    """Every external script the prototype loads: the manifest's libraries and any CDN URL in a part."""
    from .prototype import LUCIDE_URL, manifest_of

    manifest, _ = manifest_of(parts)
    found = [str(u) for u in manifest.get("libraries") or []]
    for path, text in sorted(parts.items()):
        if path == "manifest.json":
            continue
        for url in _URL_RE.findall(text or ""):
            if url not in found and url != LUCIDE_URL:
                found.append(url)
    return found


# ---------------------------------------------------------------------------
# Change map: what changed against the baseline (template mode, T4)
# ---------------------------------------------------------------------------

# Share of a screen's lines that changed above which it is "rewritten" (a full port) rather than
# "edited" (port the patch). Plan §11 open question; a fixed share keeps the tag computed.
REWRITE_SHARE = 0.6
GLOBAL_PARTS = ("tokens.css", "app.css", "shell.js")
CHANGE_TAGS = ("unchanged", "restyled", "edited", "rewritten", "new")


def _lines(text: str) -> list[str]:
    """A part as diff lines: markup is split between tags, so one long line of HTML diffs by
    element rather than as a whole."""
    return re.sub(r">(?=<)", ">\n", text or "").splitlines(keepends=True)


def _screen_text(parts: dict, manifest: dict, sid: str) -> str:
    """Everything that is one screen's own: its manifest entry, its script and its stylesheet."""
    entry = next((s for s in manifest.get("screens") or [] if s.get("id") == sid), None)
    return "".join(
        [
            json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n"
            if entry
            else "",
            parts.get(f"screens/{sid}.js") or "",
            parts.get(f"screens/{sid}.css") or "",
        ]
    )


def _is_screen_part(path: str) -> bool:
    return path.startswith("screens/")


def change_map(
    parts: dict, baseline_parts: dict | None, label: str = ""
) -> tuple[dict, dict]:
    """``(changes, patches)``: per screen of ``parts``, how it differs from ``baseline_parts``.

    changes = {"baseline", "global": {part: changed|unchanged, "other": …}, "screens": {id: tag},
               "removed": [ids]}; patches = {screen id: unified diff} for edited screens.
    Tags: unchanged (identical, no global change), restyled (identical, the global look changed),
    edited (changed, mostly the same markup), rewritten (mostly new), new (not in the baseline).
    """
    import difflib

    from .prototype import manifest_of

    base = baseline_parts or {}
    manifest, _ = manifest_of(parts)
    base_manifest, _ = manifest_of(base) if base else ({}, [])
    base_ids = {s.get("id") for s in base_manifest.get("screens") or []}

    glob = {
        p: ("changed" if (parts.get(p) or "") != (base.get(p) or "") else "unchanged")
        for p in GLOBAL_PARTS
    }
    # Shared parts other than those (data.js, lib/*, imported/*): any change counts as global.
    # (The kit page's YAML and bridge are not its look: the build follows the spec, so a change there
    # is the spec's change, not a restyle.)
    from .prototype_kit import BRIDGE_PART, SPEC_PART

    others = sorted(
        p
        for p in set(parts) | set(base)
        if p not in GLOBAL_PARTS
        and p not in (SPEC_PART, BRIDGE_PART)
        and p != "manifest.json"
        and not _is_screen_part(p)
    )
    glob["other"] = (
        "changed"
        if any((parts.get(p) or "") != (base.get(p) or "") for p in others)
        else "unchanged"
    )
    if base and (
        manifest.get("fonts"),
        manifest.get("libraries"),
        manifest.get("roles"),
    ) != (
        base_manifest.get("fonts"),
        base_manifest.get("libraries"),
        base_manifest.get("roles"),
    ):
        glob["other"] = "changed"
    look_changed = any(v == "changed" for v in glob.values())

    screens: dict = {}
    patches: dict = {}
    for s in manifest.get("screens") or []:
        sid = s.get("id")
        if not sid:
            continue
        if not base or sid not in base_ids:
            screens[sid] = "new"
            continue
        now, before = (
            _screen_text(parts, manifest, sid),
            _screen_text(base, base_manifest, sid),
        )
        if now == before:
            screens[sid] = "restyled" if look_changed else "unchanged"
            continue
        a, b = _lines(before), _lines(now)
        ratio = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
        if 1 - ratio > REWRITE_SHARE:
            screens[sid] = "rewritten"
        else:
            screens[sid] = "edited"
            patches[sid] = "".join(
                difflib.unified_diff(
                    a,
                    b,
                    fromfile=f"baseline/screens/{sid}",
                    tofile=f"approved/screens/{sid}",
                )
            )
    changes = {
        "baseline": label or ("none" if not base else "baseline"),
        "global": glob,
        "screens": screens,
        "removed": sorted(i for i in base_ids if i and i not in screens),
    }
    return changes, patches


def write_change_map(out_dir, parts: dict, baseline) -> dict:
    """changes.json and screens/<id>/diff.patch under ``out_dir``; ``baseline`` is (label, parts)."""
    label, base = baseline if baseline else ("", {})
    changes, patches = change_map(parts, base, label)
    out = Path(out_dir)
    (out / "changes.json").write_text(json.dumps(changes, indent=2), encoding="utf-8")
    for sid, patch in patches.items():
        folder = out / "screens" / sid
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "diff.patch").write_text(patch, encoding="utf-8")
    return changes


def write_prototype_bundle(
    parts: dict, out_dir, *, design=None, python=None, soon=None, baseline=None
) -> dict:
    """``out_dir`` (``.zas/bundle/prototype``) for an open-mode requirement; returns capture.json.

    prototype.html, manifest.json, design.json, libraries.json, index.md, and per manifest screen
    ``screens/<id>/dom.<role>.html``, ``shot.<role>.png`` and ``css.used.css``.
    """
    import os
    import signal
    import subprocess
    import sys

    from .preview_probe import WORKER, playwright_available
    from .prototype import assemble, manifest_of, parts_hash

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest, _ = manifest_of(parts)
    (out / "prototype.html").write_text(assemble(parts, soon), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "design.json").write_text(
        json.dumps(design or {}, indent=2), encoding="utf-8"
    )
    (out / "libraries.json").write_text(
        json.dumps(prototype_libraries(parts), indent=2), encoding="utf-8"
    )
    capture = {
        "version": 1,
        "prototype_hash": parts_hash(parts),
        "source": manifest.get("source") or "generated",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "probe": "ok",
        "screens": [],
    }
    python = python or sys.executable
    if not playwright_available(python):
        capture["probe"] = "unavailable: Playwright is not installed"
    else:
        proc = subprocess.Popen(
            [python, str(WORKER), "--open", str(out / "prototype.html"), str(out)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            start_new_session=True,  # killing its group takes Chromium too
        )
        try:
            stdout, _ = proc.communicate(timeout=PROTOTYPE_CAPTURE_TIMEOUT)
            lines = [line for line in (stdout or "").splitlines() if line.strip()]
            result = json.loads(lines[-1]) if lines else {}
            if not result.get("ok", False) and "screens" not in result:
                capture["probe"] = f"failed: {result.get('error') or 'no result'}"
            for key in ("screens", "load_errors", "blocked"):
                capture[key] = result.get(key) or capture.get(key) or []
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            capture["probe"] = f"failed: took longer than {PROTOTYPE_CAPTURE_TIMEOUT} s"
        except (ValueError, OSError) as exc:
            capture["probe"] = f"failed: {exc}"
    (out / "capture.json").write_text(json.dumps(capture, indent=2), encoding="utf-8")
    # Template mode: what changed against the baseline, so the build ports only that.
    changes = write_change_map(out, parts, baseline) if baseline is not None else None
    if changes is not None:
        capture["changes"] = changes
    (out / "index.md").write_text(
        prototype_index_md(capture, manifest, design, changes=changes), encoding="utf-8"
    )
    return capture


def prototype_index_md(capture: dict, manifest: dict, design=None, changes=None) -> str:
    """The table the build reads first: every prototype screen, its roles and its files."""
    tokens = (design or {}).get("tokens") or {}
    fonts = (design or {}).get("fonts") or {}
    lines = [
        "# Approved prototype",
        "",
        f"Source: {capture.get('source')} prototype · hash {capture.get('prototype_hash', '')[:12]} · "
        f"probe: {capture.get('probe')}",
        "",
        "What the user approved, screen by screen: `shot.<role>.png` (how it looks) and "
        "`dom.<role>.html` (what it rendered). Port, don't redraw (`references/open-mode.md`): each "
        "screen's component is in the prototype's source (`source/index.md`: each script, what it "
        'defines by line); copy its markup, classes and inline styles under <div className="zp">, '
        "which `frontend/src/custom/prototype.css` (the prototype's stylesheets, scoped) styles, with the "
        "app's data. Its router, store and timers are not used. Behaviour comes from the spec.",
        "Screens marked prototype-only are not built. The app's kit is for kit pages "
        '(`references/open-mode.md`, "The kit"); rebuild screens are ported and need none.',
        "",
        "Design (`design.json`, from `app.design`): "
        + (
            f"brand {tokens.get('brand', '?')}, fonts "
            + ", ".join(f"{k} {v}" for k, v in fonts.items())
            + f", {len(tokens)} tokens."
            if tokens
            else "not recorded in the spec; read the `:root` variables in `prototype.html`."
        ),
        "",
    ]
    tags = (changes or {}).get("screens") or {}
    if changes is not None:
        glob = changes.get("global") or {}
        changed = [k for k, v in glob.items() if v == "changed"]
        lines += [
            f"**Change map** (`changes.json`) against {changes.get('baseline')}: read the Change "
            "column first and do only what it says (`references/open-mode.md`, \"Change map\"). "
            + (
                "Shared look changed: " + ", ".join(f"`{c}`" for c in changed) + "."
                if changed
                else "The shared look (tokens.css, app.css, shell) did not change."
            )
            + (
                " Removed screens: "
                + ", ".join(f"`{r}`" for r in changes["removed"])
                + "."
                if changes.get("removed")
                else ""
            ),
            "",
        ]
    lines += [
        "| Screen | Title | Roles | Record | Files | Problems |"
        + (" Change |" if changes is not None else ""),
        "|---|---|---|---|---|---|" + ("---|" if changes is not None else ""),
    ]
    for s in capture.get("screens") or []:
        shot_roles = [r["role"] for r in s.get("roles") or [] if r.get("files")]
        shared = [
            f"{r['role']}={r['same_as']}"
            for r in s.get("roles") or []
            if r.get("same_as")
        ]
        problems = []
        for r in s.get("roles") or []:
            if r.get("error"):
                problems.append(f"{r['role']}: did not open ({r['error'][:120]})")
            for e in r.get("errors") or []:
                problems.append(f"{r['role']}: {e[:120]}")
            if r.get("blank"):
                problems.append(f"{r['role']}: blank")
        roles = ", ".join(shot_roles) + (
            f" (same: {', '.join(shared)})" if shared else ""
        )
        record = (
            f"{s.get('record')} ({next((r['record'] for r in s.get('roles') or [] if r.get('record')), 'none')})"
            if s.get("record")
            else ""
        )
        title = (s.get("title") or "").replace("|", "/")
        if s.get("only") == "prototype":
            title += " · prototype-only"
        files = f"screens/{s['id']}/" if shot_roles else "none"
        change = ""
        if changes is not None:
            tag = tags.get(s["id"], "new")
            change = f" {tag}" + (" (`diff.patch`)" if tag == "edited" else "") + " |"
        lines.append(
            f"| `{s['id']}` | {title} | {roles or '-'} | {record} | {files} | "
            + ("; ".join(problems[:3]).replace("|", "/") or "")
            + " |"
            + change
        )
    no_ref = [
        s["id"]
        for s in capture.get("screens") or []
        if s.get("only") != "prototype"
        and any(r.get("blank") or r.get("error") for r in s.get("roles") or [])
    ]
    if no_ref:
        lines += [
            "",
            "**No reference** for: "
            + ", ".join(f"`{x}`" for x in no_ref)
            + ". Their snapshot is "
            "blank, so there is no look to port: build them from the spec in the look of the screens "
            "that have one, and don't read their blank `shot.*.png` as the design.",
        ]
    if capture.get("load_errors"):
        lines += [
            "",
            "Errors while the page loaded:",
            *[f"- {e}" for e in capture["load_errors"][:10]],
        ]
    if capture.get("blocked"):
        lines += [
            "",
            "Blocked requests (not on the allowed hosts):",
            *[f"- {u}" for u in capture["blocked"][:10]],
        ]
    # The shell is in every snapshot; each role's home shows it with that role's menu.
    homes = manifest.get("home") if isinstance(manifest.get("home"), dict) else {}
    shot = {
        (s["id"], r["role"]): r.get("same_as") or r["role"]
        for s in capture.get("screens") or []
        for r in s.get("roles") or []
        if r.get("files") or r.get("same_as")
    }
    shell_refs = [
        f"{role} `screens/{home}/shot.{shot[(home, role)]}.png`"
        for role, home in homes.items()
        if (home, role) in shot
    ]
    lines += [
        "",
        "Shell (sidebar or top bar, app name, menu groups, user card): build it as "
        "`src/custom/Shell.tsx` on the runtime's `makeShell` (references/open-mode.md, "
        '"The shell"). Only its look comes from here; the menu is the spec\'s per role.'
        + (
            " Read it on each role's home: " + ", ".join(shell_refs) + "."
            if shell_refs
            else ""
        ),
    ]
    lines += [
        "",
        "Libraries the prototype loads are in `libraries.json`: use the npm package of the same "
        "library, or redraw with zas / SVG, and say which in the build report.",
        "",
    ]
    return "\n".join(lines)
