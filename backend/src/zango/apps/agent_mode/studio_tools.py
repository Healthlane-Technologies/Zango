"""Tools the App Studio build agent calls during its own session.

``studio_verify``: the agent builds the app a slice at a time (one record with its pages and
screens) and checks each slice before it starts the next. The platform brings the app up and runs
the test layers on that slice's spec paths only (zas_test ZAS_TEST_SCOPE), and the agent gets the
same brief a fix round would, while it still has the slice in mind.

``report_platform_issue``: a failure the agent traced to the platform (zas_core, zas_test, a
package) rather than the app. It is recorded for the platform team, and the check is taken out
of the fix rounds; the agent must not patch the runtime to make it pass.

Threading is the same as spec_tools: the tools run on the SDK pump's loop and must not touch the
ORM or the tenant connection. A call is handed to the run's main thread through the stream queue
(kind "tool_call"); the main thread runs it (``handle_call``) and sets the reply, which the tool
waits for off the loop.
"""

from __future__ import annotations

import asyncio
import logging
import threading

from dataclasses import dataclass, field
from typing import Any


logger = logging.getLogger("zango.agent_mode")

SERVER_NAME = "zas_build"
TOOL_NAMES = [
    f"mcp__{SERVER_NAME}__studio_verify",
    f"mcp__{SERVER_NAME}__report_platform_issue",
]
# Bring-up (~15 s) plus the API, UI, parity and scenario checks of one slice.
VERIFY_TIMEOUT = 20 * 60
# The layers a slice is checked with; the shell, views and lint are checked once, at the end.
SLICE_LAYERS = {"api": [], "ui": [], "design": ["parity", "kit"], "scenarios": []}
MAX_PATHS = 12


@dataclass
class ToolCall:
    """One tool call waiting for the main thread."""

    name: str
    args: dict
    done: threading.Event = field(default_factory=threading.Event)
    result: str = ""

    def reply(self, text: str) -> None:
        self.result = text
        self.done.set()


def build_studio_server(push):
    """The in-process MCP server for a build run. ``push(kind, payload)`` is the stream's."""
    from claude_agent_sdk import create_sdk_mcp_server, tool

    async def ask(name: str, args: dict, timeout: float) -> dict:
        call = ToolCall(name=name, args=dict(args or {}))
        push("tool_call", call)
        loop = asyncio.get_running_loop()
        finished = await loop.run_in_executor(None, call.done.wait, timeout)
        text = (
            call.result
            if finished
            else f"{name} took longer than {int(timeout)} s; carry on."
        )
        return {"content": [{"type": "text", "text": text}]}

    @tool(
        "studio_verify",
        "Bring the app up and run the platform's checks (API, UI flows, prototype parity, "
        "scenarios) on one build slice: the spec paths you just built, e.g. "
        '["entities.case", "pages.my_cases", "detail_views.case_360"]. Call it after each slice, '
        'fix what it reports, then start the next slice. Free design: ["kit"] compares each kit '
        "piece with the prototype's. Takes a few minutes.",
        {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Spec paths of the slice: entities.<code>, pages.<code>, "
                    "detail_views.<code>, or kit (the app's kit pieces, Free design).",
                },
            },
            "required": ["paths"],
        },
    )
    async def studio_verify(args):
        return await ask("studio_verify", args, VERIFY_TIMEOUT + 60)

    @tool(
        "report_platform_issue",
        "Report a failing check whose cause is in the platform (backend/zas_core, zas_test, a "
        "package), not in the app's code. Give the check id, what is wrong and where. The check "
        "leaves the fix rounds and goes to the platform team. Never patch the runtime instead.",
        {
            "type": "object",
            "properties": {
                "check_id": {"type": "string"},
                "what": {
                    "type": "string",
                    "description": "The platform bug, in one or two sentences.",
                },
                "where": {
                    "type": "string",
                    "description": "File and line, e.g. zas_core/expr.py:526.",
                },
            },
            "required": ["check_id", "what"],
        },
    )
    async def report_platform_issue(args):
        return await ask("report_platform_issue", args, 30)

    return create_sdk_mcp_server(
        name=SERVER_NAME, version="1.0.0", tools=[studio_verify, report_platform_issue]
    )


def _paths(args: dict) -> list[str]:
    raw = args.get("paths") or []
    if isinstance(raw, str):
        raw = [raw]
    out = []
    for p in raw:
        p = str(p).strip().strip("/").replace("/", ".")
        if (
            p == "kit" or p.startswith(("entities.", "pages.", "detail_views.", "kit."))
        ) and p not in out:
            out.append(p)
    return out[:MAX_PATHS]


def verify_slice(studio, creds: dict, paths: list[str], emit=None) -> str:
    """Bring up, then the slice's checks; the brief the agent gets back."""
    from .studio_status import without_harness

    ok = studio.bring_up(creds, emit)
    layers = studio.verify(emit, only=dict(SLICE_LAYERS), bring_up_ok=ok, scope=paths)
    layers = without_harness(layers)
    reported = set(studio.platform_issue_ids())
    for layer in layers.values():
        keep = [f for f in layer.failures if f.get("id") not in reported]
        if len(keep) != len(layer.failures):
            layer.failures = keep
            if not keep and layer.status == "fail":
                layer.status = "pass"
    counts = {
        name: layer.counts or {}
        for name, layer in layers.items()
        if layer.status != "skip"
    }
    head = (
        "Slice "
        + ", ".join(paths)
        + ": "
        + (
            "; ".join(
                f"{n} {c.get('pass', 0)} passed, {c.get('fail', 0)} failed"
                for n, c in counts.items()
            )
            or "no checks ran"
        )
    )
    skipped = [
        f"{n} skipped ({x.reason})" for n, x in layers.items() if x.status == "skip"
    ]
    if ok and not any(x.status == "fail" for x in layers.values()):
        return (
            head
            + ("\n" + "\n".join(skipped) if skipped else "")
            + ("\nThe slice works. Start the next one.")
        )
    brief = studio.digest(ok, layers).replace(
        "## Fix round: the platform's checks found problems",
        "## This slice's checks found problems",
    )
    return (
        head
        + ("\n" + "\n".join(skipped) if skipped else "")
        + "\n\n"
        + brief
        + "\nFix these, then call studio_verify on the same paths again. If a failure is the "
        "platform's (zas_core, zas_test, a package), call report_platform_issue instead of working "
        "around it."
    )


def handle_call(call: ToolCall, *, studio, tenant, service_account, emit=None) -> None:
    """Run one tool call on the main thread (the tenant connection) and reply to it."""
    try:
        if call.name == "studio_verify":
            paths = _paths(call.args)
            if not paths:
                call.reply(
                    "Give the slice's spec paths: entities.<code>, pages.<code>, detail_views.<code>."
                )
                return
            if emit:
                emit(
                    "sys",
                    "Checking a build slice: " + ", ".join(paths) + ".",
                    level="sys",
                )
            if getattr(
                studio, "live_creds", None
            ):  # a fix round: finish() holds the account
                call.reply(verify_slice(studio, studio.live_creds, paths, emit))
            else:
                with service_account(tenant, emit=emit) as creds:
                    call.reply(verify_slice(studio, creds, paths, emit))
        elif call.name == "report_platform_issue":
            issue = {
                "check_id": str(call.args.get("check_id") or "")[:200],
                "what": str(call.args.get("what") or "")[:1000],
                "where": str(call.args.get("where") or "")[:300],
            }
            studio.add_platform_issue(issue)
            if emit:
                emit(
                    "sys",
                    f"Platform issue reported: {issue['check_id']}: {issue['what'][:200]}",
                    level="warn",
                )
            call.reply(
                "Recorded for the platform team. That check is out of the fix rounds; don't work "
                "around it. Carry on with the rest."
            )
        else:
            call.reply(f"Unknown tool {call.name}.")
    except Exception as exc:  # noqa: BLE001 - the agent must always get an answer
        logger.exception("agent_mode: build tool %s failed", call.name)
        call.reply(
            f"{call.name} could not run ({type(exc).__name__}: {exc}). Carry on; the "
            "platform checks everything after your turn."
        )


def is_tool_call(payload: Any) -> bool:
    return isinstance(payload, ToolCall)
