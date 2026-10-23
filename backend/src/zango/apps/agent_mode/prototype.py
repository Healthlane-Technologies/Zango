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
# Parts copied from an uploaded HTML file (imported/*, body.html) keep the file's own
# scripts whole: a script cannot be split into separately parsed parts.
MAX_IMPORTED_PART_BYTES = 1_000_000
MAX_TOTAL_BYTES = 2_000_000
MAX_READ_LINES = 400
MAX_FIND_HITS = 20

PART_RE = re.compile(
    r"^[a-z0-9][a-z0-9_.-]*(/[a-z0-9][a-z0-9_.-]*){0,2}\.(css|js|json)$"
)
# The markup of an imported page's body; the only HTML part.
BODY_PART = "body.html"
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
    if is_imported(manifest):
        return False
    return any(screen_part(s["id"]) not in parts for s in manifest.get("screens", []))


def is_imported(manifest: dict) -> bool:
    """An uploaded page: its screens are drawn by its own code, not screens/<id>.js."""
    return manifest.get("source") == "imported"


def part_limit(path: str) -> int:
    return (
        MAX_IMPORTED_PART_BYTES
        if path == BODY_PART or path.startswith("imported/")
        else MAX_PART_BYTES
    )


def static_problems(parts: dict) -> list[str]:
    """Everything assembly can tell without running the page."""
    manifest, problems = manifest_of(parts)
    ids = [s["id"] for s in manifest.get("screens", [])]
    if manifest and is_imported(manifest):
        if "ZAS.ready" not in "".join(t for p, t in parts.items() if p.endswith(".js")):
            problems.append(
                "Imported page: no part calls ZAS.ready({go}) yet, so the preview cannot open "
                "its screens or report where the user is (see the zango-prototype skill)."
            )
        unsampled = [
            s["id"]
            for s in manifest.get("screens", [])
            if s.get("record") and not s.get("sample")
        ]
        if unsampled:
            problems.append(
                'Imported page: record screens with no "sample" record id in manifest.json '
                "(the build's snapshots open them with it): " + ", ".join(unsampled)
            )
    elif manifest:
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
    out.append("</head><body>")
    if parts.get(BODY_PART):
        out.append(parts[BODY_PART].replace("</body", "<\\/body"))
    out.append('<div id="zas-app"></div>')
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
# Importing an uploaded HTML page
# ---------------------------------------------------------------------------

# Script and style elements in document order. finditer never looks inside a match, so a
# "<style" written in a script's string is part of that script, as the browser parses it.
_ELEMENT_RE = re.compile(r"<(script|style)\b([^>]*)>(.*?)</\1\s*>", re.I | re.S)
_ATTR_RE = re.compile(r'([a-zA-Z-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))')
_JS_TYPES = ("", "text/javascript", "application/javascript", "module")


def _attrs(raw: str) -> dict:
    return {
        m.group(1).lower(): next(g for g in m.groups()[1:] if g is not None)
        for m in _ATTR_RE.finditer(raw or "")
    }


def import_html(html: str) -> tuple[dict, list[str]]:
    """An uploaded page as prototype parts, kept as it is, and notes on what changed.

    Styles go to imported/styles.css, each inline script to imported/script-NN.js (in
    order), allowed library scripts and Google Fonts to the manifest, and the rest of the
    markup to body.html. A starter manifest marks the prototype as imported.
    """
    notes: list[str] = []
    styles: list[str] = []
    scripts: list[str] = []
    libraries: list[str] = []
    kept: list[
        str
    ] = []  # non-JS script elements (JSON data, templates) stay in the body
    for m in _ELEMENT_RE.finditer(html):
        tag, attrs, body = m.group(1).lower(), _attrs(m.group(2)), m.group(3)
        if tag == "style":
            styles.append(body)
            continue
        kind = attrs.get("type", "").strip().lower()
        if attrs.get("src"):
            src = attrs["src"]
            if src.startswith(LIBRARY_HOSTS):
                libraries.append(src)
            else:
                notes.append(
                    f"Dropped a script from a host the preview does not allow: {src}"
                )
        elif kind in _JS_TYPES:
            if kind == "module":
                notes.append(
                    "A module script now runs as a classic script; check it still works."
                )
            scripts.append(body)
        else:
            kept.append(m.group(0))
    rest = _ELEMENT_RE.sub("", html)
    fonts = [
        _attrs(m.group(1)).get("href", "")
        for m in re.finditer(r"<link\b([^>]*)>", rest, re.I)
        if _attrs(m.group(1)).get("href", "").startswith(FONT_HOST)
    ]
    title_m = re.search(r"<title[^>]*>(.*?)</title>", rest, re.I | re.S)
    title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else "Prototype"
    body_m = re.search(r"<body\b[^>]*>(.*)</body\s*>", rest, re.I | re.S)
    body = body_m.group(1) if body_m else rest
    # What the page shell already provides, or the preview does not allow.
    body = re.sub(
        r"<!doctype[^>]*>|</?(html|head|body)\b[^>]*>|<meta\b[^>]*>|<link\b[^>]*>"
        r"|<title[^>]*>.*?</title>|<base\b[^>]*>",
        "",
        body,
        flags=re.I | re.S,
    ).strip()
    body = "\n".join([*kept, body]).strip()
    manifest = {
        "title": title,
        "source": "imported",
        "fonts": fonts,
        "libraries": libraries,
        "roles": {},
        "screens": [],
    }
    parts = {"manifest.json": json.dumps(manifest, indent=2, ensure_ascii=False)}
    if styles:
        parts["imported/styles.css"] = "\n\n".join(styles)
    for i, script in enumerate(scripts, 1):
        parts[f"imported/script-{i:02d}.js"] = script
    if body:
        parts[BODY_PART] = body
    return parts, notes


# ---------------------------------------------------------------------------
# The workbench the tools edit
# ---------------------------------------------------------------------------


class PrototypeBench:
    """The prototype's parts for this turn, and every write applied to them."""

    def __init__(self, parts: dict | None, emit, documents: dict | None = None):
        self.parts: dict = {str(k): str(v or "") for k, v in (parts or {}).items()}
        # Uploaded HTML files by name ({name: html}), for proto_import.
        self.documents: dict = dict(documents or {})
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
        if part != BODY_PART and not PART_RE.match(part):
            raise ProtoRefused(
                f"`{part}` is not a valid part path: lower-case a-z 0-9 . _ -, at most two folders, "
                "ending .css, .js or .json (e.g. screens/request.view.js)."
            )
        return part

    def _commit(self, new_parts: dict, touched: list[str], verb: str) -> str:
        for path in touched:
            limit = part_limit(path)
            if path in new_parts and len(new_parts[path].encode()) > limit:
                raise ProtoRefused(
                    f"Not written: {path} would be {len(new_parts[path].encode()) // 1000} KB; the "
                    f"limit is {limit // 1000} KB per part. Split it (e.g. a screen's "
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

    def import_document(self, document: str) -> str:
        name = (document or "").strip()
        match = next(
            (n for n in self.documents if n.lower() == name.lower()),
            next((n for n in self.documents if name.lower() in n.lower()), None)
            if name
            else None,
        )
        if match is None:
            known = ", ".join(self.documents) or "none"
            raise ProtoRefused(f"No uploaded HTML file `{name}`. HTML files: {known}.")
        imported, notes = import_html(self.documents[match])
        # The page replaces any earlier import; parts the analyst added stay.
        new = {
            p: t
            for p, t in self.parts.items()
            if not (p.startswith("imported/") or p == BODY_PART)
        }
        if "manifest.json" in new:
            imported.pop("manifest.json")
        new.update(imported)
        out = self._commit(new, sorted(imported), f"Imported {match} as")
        return (
            out
            + ("\nNotes:\n" + "\n".join(f"- {n}" for n in notes) if notes else "")
            + (
                "\nNext: fill manifest.json (screens with ids, roles) from the page's own navigation "
                "and personas, then write a small part (e.g. zas-bridge.js) that calls "
                "ZAS.ready({go(screen, {role, record}) {...}}) using the page's own router, and "
                "ZAS.at(screen, {role}) after it navigates. Do not rewrite the page."
            )
        )


# ---------------------------------------------------------------------------
# Design tokens (app.design in the spec)
# ---------------------------------------------------------------------------
# The build themes the zas runtime from app.design.tokens (Stage 2, B2), so the
# canonical names below are what it maps onto --z-*. A prototype's own names are
# matched through _TOKEN_ALIASES; tokens with no alias keep their own name.

DESIGN_TOKENS = (
    "brand", "brand-strong", "brand-soft", "accent", "accent-soft",
    "page", "card", "sunk", "nav",
    "text-strong", "text", "text-2", "text-3", "text-faint",
    "border-faint", "border", "border-strong",
    "ok", "ok-bg", "warn", "warn-bg", "bad", "bad-bg", "info", "info-bg",
    "radius-sm", "radius", "radius-lg",
    "shadow-sm", "shadow", "shadow-lg",
)  # fmt: skip
_TOKEN_ALIASES = {
    "page": ("surface-page", "bg", "background", "surface-bg"),
    "card": ("surface-card", "surface", "panel"),
    "sunk": ("surface-sunken", "sunken", "surface-sunk", "muted-bg"),
    "nav": ("surface-nav", "sidebar"),
    "text": ("ink", "fg", "foreground", "text-body"),
    "text-2": ("ink-2", "text-sub", "text-secondary"),
    "text-3": ("ink-3", "text-muted", "muted"),
    "text-faint": ("ink-4",),
    "border": ("line", "rule"),
    "border-strong": ("line-strong", "rule-2"),
    "border-faint": ("line-faint",),
    "radius": ("r", "r-md", "radius-md"),
    "radius-sm": ("r-sm",),
    "radius-lg": ("r-lg",),
    "shadow": ("shadow-md",),
    "brand-strong": ("brand-dark", "brand-700"),
    "brand-soft": ("brand-light", "brand-50"),
    "ok": ("success",),
    "ok-bg": ("success-bg",),
    "warn": ("warning",),
    "warn-bg": ("warning-bg",),
    "bad": ("danger", "error"),
    "bad-bg": ("danger-bg", "error-bg"),
}
_FONT_VARS = {
    "body": ("font", "font-body", "font-sans", "sans", "body-font"),
    "display": ("display", "font-display", "font-heading", "heading-font"),
    "mono": ("mono", "font-mono", "code-font"),
}
_DECL_RE = re.compile(r"--([a-zA-Z0-9_-]+)\s*:\s*([^;]+?)\s*(?:;|$)", re.S)
_VAR_RE = re.compile(r"var\(\s*--([a-zA-Z0-9_-]+)\s*(?:,\s*([^()]*))?\)")


def _root_vars(css: str) -> dict:
    """Custom properties on top-level ``:root`` rules (not inside @media), later rules winning."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    found: dict = {}
    depth, start = 0, 0
    for i, ch in enumerate(css):
        if ch == "{":
            if depth == 0:
                selector, start = css[start:i].strip(), i + 1
                is_root = selector.rsplit("}", 1)[-1].strip() == ":root"
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                if is_root:
                    for name, value in _DECL_RE.findall(css[start:i]):
                        found[name.lower()] = " ".join(value.split())
                start = i + 1
            depth = max(depth, 0)
    return found


def _resolve(value: str, env: dict, depth: int = 0) -> str:
    if depth > 8 or "var(" not in value:
        return value

    def sub(m):
        name, fallback = m.group(1).lower(), m.group(2)
        if name in env:
            return _resolve(env[name], env, depth + 1)
        return fallback.strip() if fallback else m.group(0)

    return _VAR_RE.sub(sub, value)


def _family(value: str) -> str:
    first = value.split(",")[0].strip().strip("'\"")
    generic = {
        "system-ui",
        "sans-serif",
        "serif",
        "monospace",
        "-apple-system",
        "ui-monospace",
    }
    return "" if first in generic or first.startswith("var(") else first


def design_tokens(parts: dict) -> dict:
    """``app.design`` pre-filled from the prototype's ``:root`` tokens.

    Generated prototypes keep their tokens in ``tokens.css``; an imported page's
    are wherever it declared them, so every stylesheet part is read. ``var()``
    chains are resolved so each token is a concrete value.
    """
    manifest, _ = manifest_of(parts)
    if not is_imported(manifest) and "tokens.css" in parts:
        sources = ["tokens.css"]
    else:
        sources = [p for p in parts if p.endswith(".css")]
    env: dict = {}
    for path in sources:
        env.update(_root_vars(parts.get(path) or ""))
    if not env:
        return {}
    values = {name: _resolve(value, env) for name, value in env.items()}

    fonts: dict = {}
    for role, names in _FONT_VARS.items():
        for name in names:
            family = _family(values.get(name, ""))
            if family:
                fonts[role] = family
                break

    tokens: dict = {}
    taken: set = set()
    for canon in DESIGN_TOKENS:
        for name in (canon, *_TOKEN_ALIASES.get(canon, ())):
            if name in values:
                tokens[canon] = values[name]
                taken.add(name)
                break
    font_names = {n for names in _FONT_VARS.values() for n in names}
    for name, value in values.items():
        if name in taken or name in font_names or name.startswith("z-"):
            continue
        tokens.setdefault(name, value)

    design: dict = {"source": "prototype"}
    if fonts:
        design["fonts"] = fonts
    design["tokens"] = tokens
    return design


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
    "proto_import",
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
        (
            "proto_import",
            "Make an uploaded HTML file the prototype, as it is: its styles, scripts and markup "
            "become parts (imported/*, body.html) and a starter manifest.json. Use it whenever "
            "the user uploaded their app as HTML, instead of redrawing it. Then complete the "
            "manifest (screens, roles) and add a small part that calls ZAS.ready({go}).",
            _schema(
                {
                    "document": {
                        "type": "string",
                        "description": "The uploaded file's name, as in the documents INDEX.md.",
                    }
                },
                ["document"],
            ),
            guarded(lambda a: pb.import_document(a.get("document", ""))),
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
