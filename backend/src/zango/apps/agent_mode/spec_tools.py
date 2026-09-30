"""Spec tools: how the analyst edits a template requirement's YAML.

Instead of re-emitting the whole journey in a fence after every answer, the
analyst changes it through small, validated tools — set a value, add an item,
remove one — and the user watches each change land in the builder panel.

Threading (see ``stream.py``): tool handlers run on the SDK pump's event loop,
on a thread whose database connection is not bound to the tenant. They must
never touch the ORM. They edit an in-memory ``SpecWorkbench`` and hand every
accepted change to the Celery main thread through ``emit``; the turn loop
there writes it to the requirement.

A change is refused — and the model told why — if it introduces a *structural*
error (wrong type, unknown value, a shape the template does not have). Missing
fields and cross-reference breaches are expected mid-interview, so they are
reported back but never block a change; ``spec_mark_ready`` is where the spec
has to be complete.
"""

from __future__ import annotations

import json
import threading

from collections.abc import Callable


MAX_RESULT_ISSUES = 25


class SpecWorkbench:
    """The draft being edited this turn, and every edit applied to it."""

    def __init__(self, text: str, template, emit: Callable[[dict], None]):
        from zango.apps.shared.app_templates.services.spec import yamlio

        self.template = template
        self.emit = emit
        self.text = text or ""
        self.changed: list[str] = []
        self.ready_summary: str | None = None
        self.edits = 0
        self._lock = threading.Lock()
        try:
            self.doc = yamlio.load_rt(self.text) if self.text.strip() else {}
        except yamlio.SpecYAMLError:
            # A draft the user broke by hand: only whole-section replacement
            # (or replacing the root) can repair it.
            self.doc = None
        if self.doc is None and not self.text.strip():
            self.doc = {}

    # -- helpers -------------------------------------------------------------

    def _plain(self, doc):
        from zango.apps.shared.app_templates.services.spec import yamlio

        return yamlio.to_plain(doc)

    def issues(self, doc=None, *, strict=False) -> list:
        from zango.apps.shared.app_templates.services.spec.validate import validate_doc

        doc = self.doc if doc is None else doc
        if doc is None:
            return [
                {
                    "level": "error",
                    "path": "",
                    "message": "The draft is not valid YAML.",
                }
            ]
        return validate_doc(self._plain(doc), self.template, strict=strict)

    def _commit(self, new_doc, changed: list[str]) -> str:
        """Apply ``new_doc`` unless it adds a structural error; return a result text."""
        from zango.apps.shared.app_templates.services.spec import yamlio
        from zango.apps.shared.app_templates.services.spec.validate import (
            structural_errors,
        )

        before = (
            {(i["path"], i.get("code")) for i in structural_errors(self.issues())}
            if self.doc is not None
            else set()
        )
        after_issues = self.issues(new_doc)
        introduced = [
            i
            for i in structural_errors(after_issues)
            if (i["path"], i.get("code")) not in before
        ]
        if introduced:
            raise ToolRefused(
                "Not applied — that would not fit the template:\n"
                + _format_issues(introduced)
            )
        self.doc = new_doc
        self.text = yamlio.dump_rt(new_doc)
        self.edits += 1
        for path in changed:
            if path not in self.changed:
                self.changed.append(path)
        self.emit(
            {
                "yaml": self.text,
                "changed_paths": list(self.changed),
                "issues": after_issues,
            }
        )
        remaining = [i for i in after_issues if i["level"] == "error"]
        note = f" {len(remaining)} error(s) remain in the spec." if remaining else ""
        return f"Done: changed {', '.join(changed) or '(root)'}.{note}"

    def _need_doc(self):
        if self.doc is None:
            raise ToolRefused(
                "The draft is not valid YAML. Replace it with spec_replace_section "
                '(path "") and the whole corrected journey.'
            )

    # -- operations (called by the tools; also directly testable) ------------

    def outline(self) -> str:
        from zango.apps.shared.app_templates.services.spec import document

        doc = self._plain(self.doc) if self.doc is not None else None
        issues = self.issues()
        lines = [
            f"Template {self.template.name} v{self.template.version}. Edits this turn: {self.edits}."
        ]
        for section in (self.template.ui_schema or {}).get("sections", []):
            pointer = section.get("pointer") or ""
            value = None
            if doc is not None and pointer:
                try:
                    value = document.get(doc, pointer)
                except document.PathError:
                    value = None
            size = (
                len(value)
                if isinstance(value, (list, dict))
                else (1 if value not in (None, "") else 0)
            )
            errs = sum(
                1
                for i in issues
                if i.get("section") == section["id"] and i["level"] == "error"
            )
            warns = sum(
                1
                for i in issues
                if i.get("section") == section["id"] and i["level"] == "warning"
            )
            state = f"{size} item(s)" if size else "empty"
            lines.append(
                f"- {section['id']} ({section.get('title', '')}) at {pointer or '/'}: {state}"
                + (f", {errs} error(s)" if errs else "")
                + (f", {warns} warning(s)" if warns else "")
            )
        return "\n".join(lines)

    def get(self, path: str = "") -> str:
        from zango.apps.shared.app_templates.services.spec import document, yamlio

        self._need_doc()
        value = document.get(self.doc, path) if path else self.doc
        concrete = document.to_pointer(document.resolve(self.doc, path)) if path else ""
        if isinstance(value, (dict, list)):
            body = yamlio.dump_rt(value)
        else:
            body = json.dumps(self._plain(value))
        return f"{concrete or '/'}:\n{body}"

    def set(self, path: str, value) -> str:
        from zango.apps.shared.app_templates.services.spec import document

        self._need_doc()
        new, changed = document.set_at(self.doc, path, value)
        return self._commit(new, changed)

    def add(self, path: str, value, index=None) -> str:
        from zango.apps.shared.app_templates.services.spec import document

        self._need_doc()
        new, changed = document.add_at(self.doc, path, value, index)
        return self._commit(new, changed)

    def remove(self, path: str) -> str:
        from zango.apps.shared.app_templates.services.spec import document

        self._need_doc()
        new, changed = document.remove_at(self.doc, path)
        return self._commit(new, changed)

    def move(self, from_path: str, to_path: str, index=None) -> str:
        from zango.apps.shared.app_templates.services.spec import document

        self._need_doc()
        new, changed = document.move_at(self.doc, from_path, to_path, index)
        return self._commit(new, changed)

    def replace_section(self, path: str, yaml_text: str) -> str:
        from zango.apps.shared.app_templates.services.spec import document, yamlio

        value = yamlio.load_rt(yaml_text)
        if not path:
            return self._commit(value if value is not None else {}, [""])
        self._need_doc()
        new, changed = document.set_at(self.doc, path, value)
        return self._commit(new, changed)

    def validate(self) -> str:
        issues = self.issues()
        if not issues:
            return "No problems found."
        return _format_issues(issues)

    def mark_ready(self, summary: str) -> str:
        self._need_doc()
        errors = [i for i in self.issues(strict=True) if i["level"] == "error"]
        if errors:
            raise ToolRefused(
                "Not ready — fix these first (ask the user where you need to):\n"
                + _format_issues(errors)
            )
        self.ready_summary = (summary or "").strip() or "The spec is complete."
        return "Marked ready. Tell the user the spec is ready for them to review and approve."


class ToolRefused(Exception):
    """A tool call the model should correct; its message is shown to it."""


def _format_issues(issues) -> str:
    shown = issues[:MAX_RESULT_ISSUES]
    lines = [f"- [{i['level']}] {i['path'] or '/'}: {i['message']}" for i in shown]
    if len(issues) > len(shown):
        lines.append(f"- … and {len(issues) - len(shown)} more (call spec_validate)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# SDK server
# ---------------------------------------------------------------------------

SERVER_NAME = "spec"
TOOL_NAMES = (
    "spec_outline",
    "spec_get",
    "spec_set",
    "spec_add",
    "spec_remove",
    "spec_move",
    "spec_replace_section",
    "spec_validate",
    "spec_mark_ready",
)
ALLOWED_TOOL_NAMES = tuple(f"mcp__{SERVER_NAME}__{name}" for name in TOOL_NAMES)

_PATH_HELP = (
    "A JSON Pointer into the journey, e.g. /roles/Manager or /masters/2/fields. "
    "In a list you may use @key instead of an index to pick the item whose "
    "code/id/name is key, or the single-key item {key: …}: /masters/@city/fields/@state."
)


def _schema(props: dict, required: list) -> dict:
    return {"type": "object", "properties": props, "required": required}


def make_handler(bench: SpecWorkbench, fn):
    """The async MCP handler for one operation: text on success, is_error on refusal."""

    async def handler(args):
        try:
            with bench._lock:
                text = fn(args or {})
            return {"content": [{"type": "text", "text": text}]}
        except Exception as exc:  # noqa: BLE001 - the model reads and corrects it
            message = (
                str(exc)
                if isinstance(exc, ToolRefused)
                else f"{type(exc).__name__}: {exc}"
            )
            return {"content": [{"type": "text", "text": message}], "is_error": True}

    return handler


def tool_specs(bench: SpecWorkbench) -> list:
    """(name, description, input schema, operation) for every spec tool."""
    path = {"type": "string", "description": _PATH_HELP}
    any_value = {
        "description": "Any JSON value: string, number, boolean, list or object."
    }
    return [
        (
            "spec_outline",
            "Every section of the journey with how full it is and its problems. Call it first each turn.",
            _schema({}, []),
            lambda a: bench.outline(),
        ),
        (
            "spec_get",
            "Read part of the journey (or all of it, with no path) as YAML.",
            _schema({"path": path}, []),
            lambda a: bench.get(a.get("path", "")),
        ),
        (
            "spec_set",
            "Set or replace the value at a path (creates missing map keys).",
            _schema({"path": path, "value": any_value}, ["path", "value"]),
            lambda a: bench.set(a["path"], a["value"]),
        ),
        (
            "spec_add",
            "Append to a list (or insert at index), or add a new key to a map.",
            _schema(
                {"path": path, "value": any_value, "index": {"type": "integer"}},
                ["path", "value"],
            ),
            lambda a: bench.add(a["path"], a["value"], a.get("index")),
        ),
        (
            "spec_remove",
            "Remove the value at a path.",
            _schema({"path": path}, ["path"]),
            lambda a: bench.remove(a["path"]),
        ),
        (
            "spec_move",
            "Move a value to another list (at index) or map key.",
            _schema(
                {"from": path, "to": path, "index": {"type": "integer"}}, ["from", "to"]
            ),
            lambda a: bench.move(a["from"], a["to"], a.get("index")),
        ),
        (
            "spec_replace_section",
            (
                "Replace everything at a path with YAML you write — for large rewrites of one section. "
                'Path "" replaces the whole journey.'
            ),
            _schema({"path": path, "yaml": {"type": "string"}}, ["path", "yaml"]),
            lambda a: bench.replace_section(a["path"], a["yaml"]),
        ),
        (
            "spec_validate",
            "Every problem in the journey right now.",
            _schema({}, []),
            lambda a: bench.validate(),
        ),
        (
            "spec_mark_ready",
            "Declare the journey complete once the interview is done. Refused while it has errors.",
            _schema({"summary": {"type": "string"}}, ["summary"]),
            lambda a: bench.mark_ready(a.get("summary", "")),
        ),
    ]


def build_spec_server(bench: SpecWorkbench):
    """An in-process MCP server exposing ``bench`` to the analyst."""
    from claude_agent_sdk import create_sdk_mcp_server, tool

    tools = [
        tool(name, description, schema)(make_handler(bench, fn))
        for name, description, schema, fn in tool_specs(bench)
    ]
    return create_sdk_mcp_server(name=SERVER_NAME, version="1.0.0", tools=tools)
