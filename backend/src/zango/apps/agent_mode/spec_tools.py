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
# Template rules that flag a custom page/tab/panel without a preview sketch.
UNSKETCHED_RULES = {"custom_page_preview", "custom_tab_preview", "custom_panel_preview"}


class SpecWorkbench:
    """The draft being edited this turn, and every edit applied to it."""

    def __init__(
        self,
        text: str,
        template,
        emit: Callable[[dict], None],
        flags=None,
        open_decisions=None,
        workflows=None,
    ):
        from zango.apps.shared.app_templates.services.spec import yamlio

        self.template = template
        self.emit = emit
        self.text = text or ""
        self.changed: list[str] = []
        self.ready_summary: str | None = None
        self.edits = 0
        self.flags: list = [dict(f) for f in flags or []]
        self.open_decisions: list = [dict(d) for d in open_decisions or []]
        self.decisions_set = False
        self.workflows: dict = dict(workflows or {})
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

    # -- provenance (one-pass drafting) ---------------------------------------

    FLAG_KINDS = ("inferred", "reference", "default", "missing")
    MAX_DECISIONS = 8

    def _emit_review(self) -> None:
        self.emit(
            {"flags": list(self.flags), "open_decisions": list(self.open_decisions)}
        )

    def flag(self, path: str, kind: str, note: str, source=None) -> str:
        from zango.apps.shared.app_templates.services.spec import document

        self._need_doc()
        if kind not in self.FLAG_KINDS:
            raise ToolRefused(f"kind must be one of {', '.join(self.FLAG_KINDS)}.")
        concrete = document.to_pointer(document.resolve(self.doc, path)) if path else ""
        entry = {"path": concrete, "kind": kind, "note": (note or "").strip()[:500]}
        if isinstance(source, dict):
            entry["source"] = {
                "document": _document_name(source.get("document")),
                "locator": str(source.get("locator") or "")[:80],
                "quote": str(source.get("quote") or "")[:400],
            }
        self.flags = [f for f in self.flags if f["path"] != concrete] + [entry]
        self._emit_review()
        return (
            f"Flagged {concrete or '/'} as {kind}. {len(self.flags)} flag(s) in total."
        )

    def unflag(self, path: str) -> str:
        from zango.apps.shared.app_templates.services.spec import document

        try:
            concrete = (
                document.to_pointer(document.resolve(self.doc, path)) if path else ""
            )
        except document.PathError:
            concrete = path
        before = len(self.flags)
        self.flags = [f for f in self.flags if f["path"] != concrete]
        self._emit_review()
        return f"Removed {before - len(self.flags)} flag(s)."

    def set_open_decisions(self, items) -> str:
        if not isinstance(items, list):
            raise ToolRefused("items must be a list.")
        if len(items) > self.MAX_DECISIONS:
            raise ToolRefused(
                f"At most {self.MAX_DECISIONS} open decisions; make the rest flags with your best assumption."
            )
        clean = []
        for i, item in enumerate(items):
            if (
                not isinstance(item, dict)
                or not str(item.get("question") or "").strip()
            ):
                raise ToolRefused(f"Decision {i + 1} needs a question.")
            options = [str(o) for o in item.get("options") or [] if str(o).strip()][:5]
            clean.append(
                {
                    "id": str(item.get("id") or f"d{i + 1}")[:40],
                    "path": str(item.get("path") or ""),
                    "question": str(item["question"]).strip()[:400],
                    "options": options,
                    "recommended": str(
                        item.get("recommended") or (options[0] if options else "")
                    )[:200],
                    "why": str(item.get("why") or "").strip()[:300],
                }
            )
        self.open_decisions = clean
        self.decisions_set = True
        self._emit_review()
        return (
            f"{len(clean)} open decision(s) recorded."
            if clean
            else "No open decisions."
        )

    # -- user journeys (swimlanes) ---------------------------------------------

    MAX_PROCESSES = 12
    MAX_NODES = 40
    NODE_KINDS = ("start", "end", "task", "event", "gateway", "message")
    FLOW_KINDS = ("sequence", "message")

    def set_workflows(self, processes) -> str:
        """Replace the narrative user journeys shown as swimlanes.

        The lifecycles in the spec are drawn by the panel itself; these are
        the journeys a person walks through (sign in, open a tab, act), which
        the spec does not spell out.
        """
        if not isinstance(processes, list):
            raise ToolRefused("processes must be a list.")
        if len(processes) > self.MAX_PROCESSES:
            raise ToolRefused(f"At most {self.MAX_PROCESSES} processes.")
        clean, ids = [], set()
        for p_i, proc in enumerate(processes, 1):
            if not isinstance(proc, dict) or not str(proc.get("title") or "").strip():
                raise ToolRefused(f"Process {p_i} needs a title.")
            pid = _slug(proc.get("id") or proc["title"]) or f"p{p_i}"
            if pid in ids:
                pid = f"{pid}_{p_i}"
            ids.add(pid)
            where = f"Process {p_i} ({proc['title']})"
            lanes, lane_ids, by_role = [], set(), {}
            for l_i, lane in enumerate(proc.get("lanes") or [], 1):
                if isinstance(lane, str):
                    lane = {"role": lane}
                role = str((lane or {}).get("role") or "").strip()
                if not role:
                    raise ToolRefused(f"{where}: lane {l_i} needs a role.")
                lid = _slug(lane.get("id") or role)
                if lid in lane_ids:
                    raise ToolRefused(f"{where}: lane {role} appears twice.")
                lane_ids.add(lid)
                by_role[_slug(role)] = lid
                lanes.append({"id": lid, "role": role[:60]})
            if not lanes:
                raise ToolRefused(f"{where} needs at least one lane.")
            raw_nodes = proc.get("nodes") or []
            if not raw_nodes or len(raw_nodes) > self.MAX_NODES:
                raise ToolRefused(f"{where} needs 1–{self.MAX_NODES} nodes.")
            nodes, node_ids = [], set()
            for n_i, node in enumerate(raw_nodes, 1):
                node = node if isinstance(node, dict) else {}
                nid = _slug(node.get("id")) or f"n{n_i}"
                kind = node.get("kind") or "task"
                lane = _slug(node.get("lane"))
                lane = lane if lane in lane_ids else by_role.get(lane, lane)
                if nid in node_ids:
                    raise ToolRefused(f"{where}: node id {nid} appears twice.")
                if kind not in self.NODE_KINDS:
                    raise ToolRefused(
                        f"{where}: node {nid} kind must be one of {', '.join(self.NODE_KINDS)}."
                    )
                if lane not in lane_ids:
                    raise ToolRefused(
                        f"{where}: node {nid} is in lane {node.get('lane')!r}, which is not one of "
                        f"{', '.join(sorted(lane_ids))}."
                    )
                node_ids.add(nid)
                entry = {
                    "id": nid,
                    "lane": lane,
                    "kind": kind,
                    "label": str(node.get("label") or "").strip()[:120],
                }
                if str(node.get("note") or "").strip():
                    entry["note"] = str(node["note"]).strip()[:160]
                nodes.append(entry)
            flows = []
            for f_i, flow in enumerate(proc.get("flows") or [], 1):
                flow = flow if isinstance(flow, dict) else {}
                src, dst = _slug(flow.get("from")), _slug(flow.get("to"))
                if src not in node_ids or dst not in node_ids:
                    raise ToolRefused(
                        f"{where}: flow {f_i} must join two of its nodes (got {flow.get('from')!r} → {flow.get('to')!r})."
                    )
                kind = flow.get("kind") or "sequence"
                if kind not in self.FLOW_KINDS:
                    raise ToolRefused(f"{where}: flow {f_i} kind must be sequence or message.")
                entry = {"from": src, "to": dst, "kind": kind}
                if str(flow.get("label") or "").strip():
                    entry["label"] = str(flow["label"]).strip()[:80]
                flows.append(entry)
            item = {
                "id": pid,
                "title": str(proc["title"]).strip()[:120],
                "source": "agent",
                "lanes": lanes,
                "nodes": nodes,
                "flows": flows,
            }
            if str(proc.get("group") or "").strip():
                item["group"] = str(proc["group"]).strip()[:80]
            clean.append(item)
        self.workflows = {"processes": clean} if clean else {}
        self.emit({"workflows": self.workflows})
        return (
            f"{len(clean)} user journey(s) recorded."
            if clean
            else "User journeys cleared."
        )

    def mark_ready(self, summary: str) -> str:
        self._need_doc()
        if self.open_decisions:
            raise ToolRefused(
                "Not ready — the user still has open decisions to answer. Clear them with "
                "spec_open_decisions once they are answered."
            )
        issues = self.issues(strict=True)
        errors = [i for i in issues if i["level"] == "error"]
        if errors:
            raise ToolRefused(
                "Not ready — fix these first (ask the user where you need to):\n"
                + _format_issues(errors)
            )
        # Every custom screen is sketched before the user is asked to review:
        # otherwise the preview shows them a placeholder where their screen goes.
        unsketched = [i for i in issues if i.get("rule") in UNSKETCHED_RULES]
        if unsketched:
            raise ToolRefused(
                "Not ready — sketch these custom screens with a `preview` first, so the user "
                "sees them in the preview:\n" + _format_issues(unsketched)
            )
        self.ready_summary = (summary or "").strip() or "The spec is complete."
        return "Marked ready. Tell the user the spec is ready for them to review and approve."


def _document_name(value) -> str:
    """The uploaded document's own name, from however the model cited it.

    On disk documents are numbered (``01-sop.pdf``) and have ``.txt``
    extracts; the panel links a citation by the name the user uploaded.
    """
    import os
    import re

    name = os.path.basename(str(value or "").strip())
    if name.endswith(".txt") and "." in name[:-4]:
        name = name[:-4]
    return re.sub(r"^\d{2}-", "", name)[:160]


def _slug(value) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")[:60]


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
    "spec_flag",
    "spec_unflag",
    "spec_open_decisions",
    "spec_set_workflows",
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
            "spec_flag",
            (
                "Record that a value was not stated in the user's material: inferred (cite the passage), "
                "reference (kept from the reference journey), default (template default) or missing."
            ),
            _schema(
                {
                    "path": path,
                    "kind": {"type": "string", "enum": list(SpecWorkbench.FLAG_KINDS)},
                    "note": {
                        "type": "string",
                        "description": "What you assumed, in plain words.",
                    },
                    "source": {
                        "type": "object",
                        "properties": {
                            "document": {"type": "string"},
                            "locator": {
                                "type": "string",
                                "description": "e.g. p. 4, sheet Orders",
                            },
                            "quote": {"type": "string"},
                        },
                    },
                },
                ["path", "kind", "note"],
            ),
            lambda a: bench.flag(
                a["path"], a["kind"], a.get("note", ""), a.get("source")
            ),
        ),
        (
            "spec_unflag",
            "Remove the flag on a path (the user confirmed it, or you now have it from their material).",
            _schema({"path": path}, ["path"]),
            lambda a: bench.unflag(a["path"]),
        ),
        (
            "spec_open_decisions",
            "Replace the list of questions only the user can answer (at most 8). Empty list when none.",
            _schema(
                {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "path": {"type": "string"},
                                "question": {"type": "string"},
                                "options": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "recommended": {"type": "string"},
                                "why": {"type": "string"},
                            },
                            "required": ["question"],
                        },
                    }
                },
                ["items"],
            ),
            lambda a: bench.set_open_decisions(a.get("items") or []),
        ),
        (
            "spec_set_workflows",
            (
                "Replace the user journeys shown to the user as swimlane diagrams: what each role does, "
                "step by step, to get something done in the app (sign in, open a tab, act, who gets "
                "notified). Not the lifecycles — the panel draws those from the journey itself."
            ),
            _schema(
                {
                    "processes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "title": {
                                    "type": "string",
                                    "description": "e.g. 3.b To upload trainings",
                                },
                                "group": {"type": "string"},
                                "lanes": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "role": {"type": "string"},
                                        },
                                        "required": ["role"],
                                    },
                                },
                                "nodes": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "lane": {
                                                "type": "string",
                                                "description": "A lane id (or role).",
                                            },
                                            "kind": {
                                                "type": "string",
                                                "enum": list(SpecWorkbench.NODE_KINDS),
                                            },
                                            "label": {"type": "string"},
                                            "note": {
                                                "type": "string",
                                                "description": "A short annotation under the node.",
                                            },
                                        },
                                        "required": ["id", "lane", "kind"],
                                    },
                                },
                                "flows": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "from": {"type": "string"},
                                            "to": {"type": "string"},
                                            "kind": {
                                                "type": "string",
                                                "enum": list(SpecWorkbench.FLOW_KINDS),
                                            },
                                            "label": {"type": "string"},
                                        },
                                        "required": ["from", "to"],
                                    },
                                },
                            },
                            "required": ["title", "lanes", "nodes", "flows"],
                        },
                    }
                },
                ["processes"],
            ),
            lambda a: bench.set_workflows(a.get("processes") or []),
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
