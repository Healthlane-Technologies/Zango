"""The approval bundle: what the user approved in the preview, for the build agent (spec-to-build F2).

The build gets the YAML; the runtime draws lists, forms, workflows and 360 pages from it. Custom
screens (custom pages, 360 tabs and panels) are written by the build agent, so for each one the
bundle keeps what the user actually saw:

    .zas/bundle/
      index.md                     what is here, screen by screen (read this first)
      manifest.json                the same as data
      screens/<screen>/
        sketch.js                  the preview sketch: port it call for call onto zas/ui.tsx
        contract.json              text, data, interactions, states, acceptance, refs
        view.<role>.json           the kit tree the sketch drew for that role, and its summary
        shot.<role>.png            the screen as that role saw it (one per distinct structure)
        in_page.<role>.png         a tab or panel in its 360 page

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
        line = "  " * depth + f"- {node['kit']}"
        if node.get("title"):
            line += f' "{node["title"]}"'
        if node.get("items"):
            line += ": " + ", ".join(node["items"])
        lines.append(line)
        lines += _outline(node.get("children") or [], depth + 1)
    return lines


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
    if probe is not None and screens:
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
            (sdir / "sketch.js").write_text(str(node["preview"]).rstrip() + "\n")
            entry["sketch"] = f"screens/{folder}/sketch.js"
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
                    "hand_written": not v.get("tree"),
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

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "index.md").write_text(index_md(manifest))
    return manifest


def index_md(manifest: dict) -> str:
    """The bundle as the build agent reads it: one section per custom screen, outline first."""
    lines = [
        "# Approval bundle",
        "",
        "What the user approved in the App Studio preview, for each custom screen. Port `sketch.js` call for",
        'call onto the zas kit (references/custom-code.md, "Porting a sketch"); the kit outline below is',
        "what the parity check compares. Screenshots show demo data: match the layout, never the numbers.",
        "Open a screenshot when a part is hand-written markup, or when parity fails.",
        "",
    ]
    if manifest.get("probe") != "ok":
        lines += [
            f"> No screenshots or kit outlines: {manifest.get('probe')}. Build from the sketch and the contract.",
            "",
        ]
    if not manifest.get("screens"):
        lines.append("No custom screens in this spec.")
    for s in manifest.get("screens") or []:
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
                    "  - hand-written markup (no kit blocks): match it from the screenshot"
                )
            else:
                lines += ["  " + ln for ln in _outline(v["tree"])]
        if s.get("in_page"):
            lines.append(f"- In its 360 page: `{s['in_page']}`")
        lines.append("")
    return "\n".join(lines)
