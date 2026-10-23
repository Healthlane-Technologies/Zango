"""Open prototype: a free HTML prototype the analyst writes next to the YAML.

In ``preview_mode == "open"`` the requirement carries a prototype of the app in any
look: its own tokens, fonts, layouts and scripts. The analyst never writes it as one
file. It writes *parts* (``manifest.json``, ``tokens.css``, ``app.css``, ``data.js``,
``shell.js``, ``screens/<id>.js`` …) through the ``proto_*`` tools, and ``assemble``
joins them into one HTML page in a fixed order. Parts keep later edits small, let
screen writers work in parallel, and give the build one file per screen.

Threading is the same as ``spec_tools``: the tools run on the SDK pump and must not
touch the ORM. ``PrototypeBench`` edits the parts in memory and hands every accepted
write to the turn loop through ``emit`` (``tasks._record_spec_edit`` saves it).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile

from functools import lru_cache
from pathlib import Path


MAX_PART_BYTES = 150_000
MAX_TOTAL_BYTES = 2_000_000
MAX_READ_LINES = 400
MAX_FIND_HITS = 20

PART_RE = re.compile(
    r"^[a-z0-9][a-z0-9_.-]*(/[a-z0-9][a-z0-9_.-]*){0,2}\.(css|js|json)$"
)
LIBRARY_HOSTS = (
    "https://cdnjs.cloudflare.com/",
    "https://cdn.jsdelivr.net/npm/",
    "https://unpkg.com/",
)
FONT_HOST = "https://fonts.googleapis.com/"
# Icons for the starter's ZAS.I(name); the prototype may load other libraries itself.
LUCIDE_URL = "https://unpkg.com/lucide@0.460.0/dist/umd/lucide.min.js"

CSP = "; ".join(
    [
        "default-src 'none'",
        "script-src 'unsafe-inline' " + " ".join(h.rstrip("/") for h in LIBRARY_HOSTS),
        "style-src 'unsafe-inline' https://fonts.googleapis.com",
        "font-src https://fonts.gstatic.com data:",
        "img-src data: blob:",
        "media-src data: blob:",
        "connect-src data: blob:",
        "form-action 'none'",
        "base-uri 'none'",
    ]
)

ASSETS_DIR = Path(__file__).resolve().parent / "prototype_assets"
_VERSION_RE = re.compile(r"@\d+(\.\d+)*|/\d+\.\d+(\.\d+)?/")


class ProtoRefused(Exception):
    """A prototype tool call the model should correct; its message is shown to it."""


@lru_cache(maxsize=1)
def runtime_js() -> str:
    """The shim and starter every assembled prototype runs on (``window.ZAS``)."""
    return (ASSETS_DIR / "zas-proto.js").read_text()


@lru_cache(maxsize=1)
def runtime_css() -> str:
    return (ASSETS_DIR / "zas-proto.css").read_text()


def parts_hash(parts: dict) -> str:
    h = hashlib.sha256()
    for path in sorted(parts):
        h.update(path.encode())
        h.update(b"\0")
        h.update((parts[path] or "").encode())
        h.update(b"\0")
    return h.hexdigest()[:32]


def total_bytes(parts: dict) -> int:
    return sum(len((t or "").encode()) for t in parts.values())


# ---------------------------------------------------------------------------
# Manifest and static checks
# ---------------------------------------------------------------------------


def manifest_of(parts: dict) -> tuple[dict, list[str]]:
    """The parsed ``manifest.json`` (or {}), and what is wrong with it."""
    text = parts.get("manifest.json")
    if text is None:
        return {}, [
            "No manifest.json yet: write it first (screens, roles, fonts, libraries)."
        ]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {}, [f"manifest.json is not valid JSON: {exc}"]
    if not isinstance(data, dict):
        return {}, ["manifest.json must be an object."]
    problems = []
    screens = data.get("screens")
    if not isinstance(screens, list) or not screens:
        problems.append(
            "manifest.json: `screens` must be a non-empty list of {id, title}."
        )
        data["screens"] = []
    else:
        seen = set()
        clean = []
        for i, s in enumerate(screens):
            if not isinstance(s, dict) or not re.fullmatch(
                r"[a-z0-9][a-z0-9_.-]*", str(s.get("id", ""))
            ):
                problems.append(
                    f"manifest.json: screens[{i}] needs an id of a-z, 0-9, . _ -"
                )
                continue
            if s["id"] in seen:
                problems.append(f"manifest.json: screen id `{s['id']}` is used twice.")
                continue
            seen.add(s["id"])
            clean.append(s)
        data["screens"] = clean
    roles = data.get("roles", {})
    if not isinstance(roles, dict):
        problems.append("manifest.json: `roles` must be an object {code: label}.")
        data["roles"] = {}
    for key, host, what in (
        ("libraries", LIBRARY_HOSTS, "cdnjs, jsdelivr (/npm/) or unpkg"),
        ("fonts", (FONT_HOST,), "fonts.googleapis.com"),
    ):
        urls = data.get(key, [])
        if not isinstance(urls, list):
            problems.append(f"manifest.json: `{key}` must be a list of URLs.")
            data[key] = []
            continue
        ok = []
        for url in urls:
            url = str(url)
            if not url.startswith(host):
                problems.append(
                    f"manifest.json: {key} URL not allowed (only {what}): {url}"
                )
            elif key == "libraries" and not _VERSION_RE.search(url):
                problems.append(f"manifest.json: pin an exact version in {url}")
            else:
                ok.append(url)
        data[key] = ok
    return data, problems


def screen_part(screen_id: str) -> str:
    return f"screens/{screen_id}.js"


def is_drafting(parts: dict) -> bool:
    """Whether the prototype is still being drawn: no parts yet, or screens with no part.

    Such a turn writes many screens, so it gets the first draft's time and budget.
    """
    if not parts:
        return True
    manifest, _ = manifest_of(parts)
    return any(screen_part(s["id"]) not in parts for s in manifest.get("screens", []))


def static_problems(parts: dict) -> list[str]:
    """Everything assembly can tell without running the page."""
    manifest, problems = manifest_of(parts)
    ids = [s["id"] for s in manifest.get("screens", [])]
    if manifest:
        missing = [i for i in ids if screen_part(i) not in parts]
        if missing:
            problems.append(
                "Screens in the manifest with no part yet: "
                + ", ".join(screen_part(i) for i in missing)
            )
        extra = sorted(
            p
            for p in parts
            if p.startswith("screens/") and p.endswith(".js") and p[8:-3] not in ids
        )
        if extra:
            problems.append(
                "Screen parts not in the manifest (not loaded): " + ", ".join(extra)
            )
    size = total_bytes(parts)
    if size > MAX_TOTAL_BYTES:
        problems.append(
            f"The prototype is {size // 1000} KB; the limit is {MAX_TOTAL_BYTES // 1000} KB."
        )
    return problems


def _node() -> str | None:
    found = shutil.which("node")
    if found:
        return found
    try:  # Playwright ships a Node runtime with its driver.
        import playwright

        candidate = Path(playwright.__file__).parent / "driver" / "node"
        return str(candidate) if candidate.exists() else None
    except Exception:  # noqa: BLE001
        return None


def js_syntax_error(source: str) -> str | None:
    """``node --check`` on one JS part; None when it parses (or Node is unavailable)."""
    node = _node()
    if not node:
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(source)
        name = fh.name
    try:
        res = subprocess.run(
            [node, "--check", name], capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    finally:
        os.unlink(name)
    if res.returncode == 0:
        return None
    lines = [ln for ln in (res.stderr or "").splitlines() if ln.strip()]
    # node prints "file:line", the offending line, a caret, then "SyntaxError: …".
    where = next((ln.rsplit(":", 1)[-1] for ln in lines[:1] if ":" in ln), "?")
    err = next(
        (ln for ln in lines if "Error" in ln), lines[-1] if lines else "SyntaxError"
    )
    return f"line {where}: {err.strip()}"


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def _esc_attr(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _ordered(parts: dict, manifest: dict) -> tuple[list[str], list[str]]:
    """(css paths, js paths) in load order."""
    screen_ids = [s["id"] for s in manifest.get("screens", [])]
    css_head = [p for p in ("tokens.css", "app.css") if p in parts]
    screen_css = [f"screens/{i}.css" for i in screen_ids if f"screens/{i}.css" in parts]
    other_css = sorted(
        p
        for p in parts
        if p.endswith(".css") and p not in css_head and p not in screen_css
    )
    js_head = [p for p in ("data.js", "shell.js") if p in parts]
    screen_js = [screen_part(i) for i in screen_ids if screen_part(i) in parts]
    other_js = sorted(
        p
        for p in parts
        if p.endswith(".js") and p not in js_head and not p.startswith("screens/")
    )
    return css_head + other_css + screen_css, js_head + other_js + screen_js


def assemble(parts: dict) -> str:
    """The prototype as one HTML page: CSP, fonts, styles, manifest, runtime, parts."""
    manifest, _ = manifest_of(parts)
    css, js = _ordered(parts, manifest)
    title = _esc_attr(manifest.get("title") or "Prototype")
    out = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}">',
        f"<title>{title}</title>",
    ]
    if manifest.get("fonts"):
        out.append(
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        )
    for url in manifest.get("fonts", []):
        out.append(f'<link rel="stylesheet" href="{_esc_attr(url)}">')
    out.append(f'<style data-zas="runtime">{runtime_css()}</style>')
    for path in css:
        body = (parts[path] or "").replace("</style", "<\\/style")
        out.append(f'<style data-part="{_esc_attr(path)}">\n{body}\n</style>')
    out.append('</head><body><div id="zas-app"></div>')
    manifest_json = json.dumps(manifest, ensure_ascii=False).replace("</", "<\\/")
    out.append(
        f'<script type="application/json" id="zas-proto">{manifest_json}</script>'
    )
    out.append(f'<script src="{LUCIDE_URL}"></script>')
    out.append(f'<script data-zas="runtime">{runtime_js()}</script>')
    for url in manifest.get("libraries", []):
        out.append(f'<script src="{_esc_attr(url)}"></script>')
    for path in js:
        # One <script> per part: a part that throws stops only itself, and its
        # sourceURL names it in the error the runtime reports.
        body = (parts[path] or "").replace("</script", "<\\/script")
        out.append(
            f'<script data-part="{_esc_attr(path)}">\n{body}\n//# sourceURL=proto/{path}\n</script>'
        )
    out.append("<script>ZAS.boot()</script>")
    out.append("</body></html>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# The workbench the tools edit
# ---------------------------------------------------------------------------


class PrototypeBench:
    """The prototype's parts for this turn, and every write applied to them."""

    def __init__(self, parts: dict | None, emit):
        self.parts: dict = {str(k): str(v or "") for k, v in (parts or {}).items()}
        self.emit = emit
        self.writes = 0
        self.written: list[str] = []

    # -- helpers -------------------------------------------------------------

    def _need(self, part: str) -> str:
        part = (part or "").strip().lstrip("/")
        if part not in self.parts:
            known = ", ".join(sorted(self.parts)) or "none yet"
            raise ProtoRefused(f"No part `{part}`. Parts: {known}.")
        return part

    def _check_path(self, part: str) -> str:
        part = (part or "").strip().lstrip("/")
        if part.startswith("proto/"):
            part = part[6:]
        if not PART_RE.match(part):
            raise ProtoRefused(
                f"`{part}` is not a valid part path: lower-case a-z 0-9 . _ -, at most two folders, "
                "ending .css, .js or .json (e.g. screens/request.view.js)."
            )
        return part

    def _commit(self, new_parts: dict, touched: list[str], verb: str) -> str:
        for path in touched:
            if path in new_parts and len(new_parts[path].encode()) > MAX_PART_BYTES:
                raise ProtoRefused(
                    f"Not written: {path} would be {len(new_parts[path].encode()) // 1000} KB; the "
                    f"limit is {MAX_PART_BYTES // 1000} KB per part. Split it (e.g. a screen's "
                    "helpers into screens/<id>.parts.js or shared code into lib/*.js)."
                )
        if total_bytes(new_parts) > MAX_TOTAL_BYTES:
            raise ProtoRefused(
                f"Not written: the prototype would exceed {MAX_TOTAL_BYTES // 1000} KB. Move large "
                "embedded images out, or trim sample data."
            )
        notes = []
        for path in touched:
            if path == "manifest.json" and path in new_parts:
                try:
                    json.loads(new_parts[path])
                except json.JSONDecodeError as exc:
                    raise ProtoRefused(
                        f"Not written: manifest.json is not valid JSON ({exc})."
                    )
            if path.endswith(".js") and path in new_parts:
                err = js_syntax_error(new_parts[path])
                if err:
                    raise ProtoRefused(
                        f"Not written: {path} does not parse, {err}. Fix and retry."
                    )
        self.parts = new_parts
        self.writes += 1
        for path in touched:
            if path not in self.written:
                self.written.append(path)
        digest = parts_hash(self.parts)
        self.emit({"prototype_parts": dict(self.parts), "prototype_hash": digest})
        problems = static_problems(self.parts)
        manifest, _ = manifest_of(self.parts)
        ids = [s["id"] for s in manifest.get("screens", [])]
        done = sum(1 for i in ids if screen_part(i) in self.parts)
        sizes = ", ".join(
            f"{p} ({len(self.parts[p].encode()) / 1000:.1f} KB)"
            for p in touched
            if p in self.parts
        )
        head = f"{verb} {sizes or ', '.join(touched)}. Prototype {total_bytes(self.parts) / 1000:.0f} KB"
        head += f", {len(self.parts)} parts, {done}/{len(ids)} screens written. The preview reloads now."
        if problems:
            notes.append("To do:\n" + "\n".join(f"- {p}" for p in problems))
        return "\n".join([head, *notes])

    # -- operations ------------------------------------------------------------

    def outline(self) -> str:
        if not self.parts:
            return (
                "No prototype yet. Start with manifest.json, tokens.css, app.css, data.js and "
                "shell.js, then screens/<id>.js (see the zango-prototype skill)."
            )
        manifest, _ = manifest_of(self.parts)
        lines = [
            f"Prototype: {total_bytes(self.parts) / 1000:.0f} KB in {len(self.parts)} parts."
        ]
        lines += [
            f"- {p} ({len(t.encode()) / 1000:.1f} KB)"
            for p, t in sorted(self.parts.items())
        ]
        if manifest.get("screens"):
            lines.append("Screens:")
            for s in manifest["screens"]:
                mark = "✓" if screen_part(s["id"]) in self.parts else "✗ no part"
                extra = " (prototype only)" if s.get("only") == "prototype" else ""
                lines.append(f"- {s['id']}: {s.get('title', '')}{extra} {mark}")
        problems = static_problems(self.parts)
        if problems:
            lines.append("To do:\n" + "\n".join(f"- {p}" for p in problems))
        return "\n".join(lines)

    def write(self, part: str, content: str) -> str:
        part = self._check_path(part)
        new = dict(self.parts)
        verb = "Replaced" if part in new else "Wrote"
        new[part] = content or ""
        return self._commit(new, [part], verb)

    def patch(self, part: str, find: str, replace: str, all_: bool = False) -> str:
        part = self._need(self._check_path(part))
        text = self.parts[part]
        if not find:
            raise ProtoRefused("`find` is empty.")
        count = text.count(find)
        if count == 0:
            raise ProtoRefused(
                f"Not found in {part}. Read the part again (proto_read) or locate the text with "
                "proto_find; `find` must match exactly, whitespace included."
            )
        if count > 1 and not all_:
            raise ProtoRefused(
                f"Found {count} times in {part}. Add surrounding text to make `find` unique, or pass "
                "all: true to replace every one."
            )
        new = dict(self.parts)
        new[part] = (
            text.replace(find, replace or "")
            if all_
            else text.replace(find, replace or "", 1)
        )
        return self._commit(new, [part], f"Patched ({count if all_ else 1}×)")

    def read(self, part: str, start: int = 1, lines: int = 200) -> str:
        part = self._need(self._check_path(part))
        rows = self.parts[part].split("\n")
        start = max(1, int(start or 1))
        lines = max(1, min(int(lines or 200), MAX_READ_LINES))
        chunk = rows[start - 1 : start - 1 + lines]
        body = "\n".join(f"{start + i:>5}  {row}" for i, row in enumerate(chunk))
        more = start - 1 + lines < len(rows)
        tail = (
            f"\n… {len(rows)} lines in all; read on from {start + lines}."
            if more
            else ""
        )
        return f"{part}, lines {start}–{start + len(chunk) - 1} of {len(rows)}:\n{body}{tail}"

    def find(self, text: str) -> str:
        if not text:
            raise ProtoRefused("`text` is empty.")
        hits = []
        needle = text.lower()
        for path in sorted(self.parts):
            for n, row in enumerate(self.parts[path].split("\n"), start=1):
                if needle in row.lower():
                    hits.append(f"{path}:{n}: {row.strip()[:160]}")
                    if len(hits) >= MAX_FIND_HITS:
                        return "\n".join(hits) + "\n… more; narrow the text."
        return "\n".join(hits) if hits else "Not found in any part."

    def remove(self, part: str) -> str:
        part = self._need(self._check_path(part))
        new = dict(self.parts)
        del new[part]
        return self._commit(new, [part], "Removed")

    def rename(self, part: str, to: str) -> str:
        part = self._need(self._check_path(part))
        to = self._check_path(to)
        if to in self.parts:
            raise ProtoRefused(f"`{to}` already exists.")
        new = dict(self.parts)
        new[to] = new.pop(part)
        return self._commit(new, [to], f"Renamed {part} →")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

PROTO_TOOL_NAMES = (
    "proto_outline",
    "proto_write",
    "proto_patch",
    "proto_read",
    "proto_find",
    "proto_remove",
    "proto_rename",
)
# What a screen writer may call: its own screen's parts, nothing in the YAML.
WRITER_TOOL_NAMES = (
    "proto_outline",
    "proto_write",
    "proto_patch",
    "proto_read",
    "proto_find",
)

_PART = {
    "type": "string",
    "description": "Part path, e.g. manifest.json, tokens.css, app.css, data.js, shell.js, "
    "screens/requests.js, screens/request.view.css, lib/charts.js.",
}


def _schema(props: dict, required: list) -> dict:
    return {"type": "object", "properties": props, "required": required}


def proto_tool_specs(pb: PrototypeBench) -> list:
    """(name, description, input schema, operation) for every prototype tool."""

    def guarded(fn):
        def run(args):
            try:
                return fn(args)
            except ProtoRefused as exc:
                from .spec_tools import ToolRefused

                raise ToolRefused(str(exc)) from exc

        return run

    return [
        (
            "proto_outline",
            "The prototype's parts with sizes, its screens (written or not) and what is left to do. "
            "Call it first in every turn that touches the prototype.",
            _schema({}, []),
            guarded(lambda a: pb.outline()),
        ),
        (
            "proto_write",
            "Create or replace one part of the prototype. Use it for new parts; change existing ones "
            "with proto_patch. JS parts must parse; manifest.json must be valid JSON.",
            _schema(
                {
                    "part": _PART,
                    "content": {"type": "string", "description": "The whole part."},
                },
                ["part", "content"],
            ),
            guarded(lambda a: pb.write(a.get("part", ""), a.get("content", ""))),
        ),
        (
            "proto_patch",
            "Replace exact text inside one part. `find` must match once (whitespace included) "
            "unless all is true. The default way to change the prototype.",
            _schema(
                {
                    "part": _PART,
                    "find": {"type": "string"},
                    "replace": {"type": "string"},
                    "all": {"type": "boolean", "description": "Replace every match."},
                },
                ["part", "find", "replace"],
            ),
            guarded(
                lambda a: pb.patch(
                    a.get("part", ""),
                    a.get("find", ""),
                    a.get("replace", ""),
                    bool(a.get("all")),
                )
            ),
        ),
        (
            "proto_read",
            "Read a part with line numbers (up to 400 lines per call).",
            _schema(
                {
                    "part": _PART,
                    "start": {
                        "type": "integer",
                        "description": "First line (default 1).",
                    },
                    "lines": {
                        "type": "integer",
                        "description": "How many (default 200).",
                    },
                },
                ["part"],
            ),
            guarded(
                lambda a: pb.read(
                    a.get("part", ""), a.get("start") or 1, a.get("lines") or 200
                )
            ),
        ),
        (
            "proto_find",
            "Find text (case-insensitive) across all parts: part, line and the line itself.",
            _schema({"text": {"type": "string"}}, ["text"]),
            guarded(lambda a: pb.find(a.get("text", ""))),
        ),
        (
            "proto_remove",
            "Delete a part.",
            _schema({"part": _PART}, ["part"]),
            guarded(lambda a: pb.remove(a.get("part", ""))),
        ),
        (
            "proto_rename",
            "Rename a part (e.g. when a screen id changes; update manifest.json too).",
            _schema({"part": _PART, "to": _PART}, ["part", "to"]),
            guarded(lambda a: pb.rename(a.get("part", ""), a.get("to", ""))),
        ),
    ]


SCREEN_WRITER_PROMPT = """\
You write one screen of an HTML prototype, as its parts, with the mcp__spec__proto_* tools.

First call proto_outline, then read manifest.json, tokens.css, app.css, data.js and shell.js
(proto_read) so your screen uses the same tokens, helpers, data and look. Then write
screens/<id>.js (and screens/<id>.css only if the screen needs its own rules) following the
zango-prototype skill's screen contract: ZAS.screen('<id>', {title, render(ctx), mount?(el, ctx)}).

Rules:
- Touch only screens/<id>.js and screens/<id>.css for the screen you were given. Never edit
  manifest.json, tokens.css, app.css, data.js or shell.js: if the screen needs something there,
  say so in your final answer and the analyst adds it.
- Use the app's tokens (var(--…)) and its shared classes; no new colour palette.
- Draw every state the brief names with the sample data (ZAS.store), and wire every action it
  names (data-act + ZAS.on) so clicking works in the preview.
- Your final answer is two or three lines: what you drew, and anything you need in shared parts.
"""


def screen_writer_agent(model: str | None = None):
    """The sub-agent that writes one screen in parallel with the others."""
    from claude_agent_sdk import AgentDefinition

    from .spec_tools import SERVER_NAME

    return AgentDefinition(
        description="Writes one screen of the open prototype (screens/<id>.js) from a brief.",
        prompt=SCREEN_WRITER_PROMPT,
        tools=[f"mcp__{SERVER_NAME}__{n}" for n in WRITER_TOOL_NAMES]
        + ["Read", "Skill"],
        mcpServers=[SERVER_NAME],
        model=model or "inherit",
        background=False,
        maxTurns=40,
    )
