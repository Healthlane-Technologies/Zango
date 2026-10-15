"""Where the user was in the preview when they wrote a message.

The App Studio preview reports where the user is (role, page, record, tab) and, after they use
"Point", the part they clicked, each with its path into the spec YAML. The console sends that
with the message; the analyst reads it under the message, so "make this bigger" or "add a
column here" arrives tied to a place in the spec.

The focus comes from the browser, so it is reduced to a small, known shape before it is stored.
"""

from __future__ import annotations


MAX_TEXT = 160
MAX_PATH = 300


def _text(value, limit: int = MAX_TEXT) -> str:
    return (
        " ".join(str(value).split())[:limit]
        if isinstance(value, (str, int, float))
        else ""
    )


def _path(value) -> str:
    path = _text(value, MAX_PATH)
    return path if path.startswith("/") else ""


def clean_focus(raw) -> dict:
    """``raw`` (from the request) as {role, page, title, path, record?, tab?, view?, pointed?}."""
    if not isinstance(raw, dict):
        return {}
    out = {
        key: value
        for key, value in (
            ("role", _text(raw.get("role"))),
            ("page", _text(raw.get("page"))),
            ("title", _text(raw.get("title"))),
            ("path", _path(raw.get("path"))),
            ("view", _text(raw.get("view"))),
        )
        if value
    }
    record = raw.get("record")
    if isinstance(record, dict) and record.get("id") is not None:
        out["record"] = {
            "entity": _text(record.get("entity")),
            "id": _text(record.get("id")),
            "label": _text(record.get("label")),
        }
    tab = raw.get("tab")
    if isinstance(tab, dict) and _path(tab.get("path")):
        out["tab"] = {"label": _text(tab.get("label")), "path": _path(tab.get("path"))}
    pointed = raw.get("pointed")
    if isinstance(pointed, dict) and _path(pointed.get("path")):
        out["pointed"] = {
            "path": _path(pointed.get("path")),
            "label": _text(pointed.get("label")),
            "text": _text(pointed.get("text"), 80),
        }
    return out if out.get("page") or out.get("pointed") else {}


def focus_note(focus, spec_doc=None) -> str:
    """The lines the analyst reads under the user's message, or "" without a focus.

    With ``spec_doc`` (the plain spec), pointing at a custom screen that has no sketch says so:
    the user is looking at a placeholder, and what they want is the screen drawn.
    """
    focus = focus or {}
    if not focus:
        return ""
    where = f'"{focus.get("title") or focus.get("page")}"'
    if focus.get("path"):
        where += f" ({focus['path']})"
    if focus.get("role"):
        where += f" as {focus['role']}"
    rec = focus.get("record")
    if rec:
        where += f", on {rec.get('entity')} #{rec.get('id')} \"{rec.get('label')}\""
    tab = focus.get("tab")
    if tab:
        where += f', tab "{tab.get("label")}" ({tab.get("path")})'
    if focus.get("view"):
        where += f", {focus['view']} view"
    lines = [f"[Preview: the user was looking at {where}."]
    pointed = focus.get("pointed")
    if pointed:
        what = pointed.get("label") or "an element"
        shown = (
            f' showing "{pointed["text"]}"'
            if pointed.get("text") and pointed["text"] != pointed.get("label")
            else ""
        )
        lines.append(
            f"They pointed at {what}{shown}: {pointed['path']}. "
            "\"This\", \"here\" and \"it\" in their message mean that part of the spec.]"
        )
        if spec_doc is not None:
            from .preview_probe import custom_screens, is_sketched

            node = custom_screens(spec_doc).get(pointed["path"])
            if node is not None and not is_sketched(node):
                lines.append(
                    "[It is a custom screen with no `preview` sketch: they are looking at a grey "
                    "placeholder showing your build text. Draw it with `preview` from the demo data, "
                    "so they see what it will actually show; rewriting `text` is not enough.]"
                )
    else:
        lines[-1] += "]"
    return "\n\n" + "\n".join(lines)
