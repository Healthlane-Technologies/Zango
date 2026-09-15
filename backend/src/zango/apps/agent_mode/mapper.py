"""Translate SDK messages into AgentRunEvent rows and run-level fields.

Field names here were read from ``claude_agent_sdk/types.py`` in the pinned
wheel. Two are easy to get wrong:

* ``SystemMessage`` is ``subtype`` + ``data``. It has no ``content``.
* ``ResultMessage`` has **no** ``total_input_tokens`` / ``total_output_tokens``.
  Token counts come from ``model_usage``, a dict keyed by model whose values
  use **camelCase** keys (``inputTokens``, ``cacheReadInputTokens``, …)
  because the CLI passes them through verbatim.

Deliberately duck-typed rather than ``isinstance``-based, so it can be unit
tested with lightweight fakes and does not require the SDK at import time.
"""

from __future__ import annotations

from .models import EventKind, EventLevel


# System subtypes emitted many times per turn that carry nothing a reader
# wants. Dropped rather than stored.
NOISY_SYSTEM_SUBTYPES = frozenset({"thinking_tokens", "token_budget", "ping"})

TOOL_RESULT_CAP = 2_000
THINKING_CAP = 2_000
TOOL_INPUT_VALUE_CAP = 4_000
# Keys whose values are file bodies — replaced by a size marker.
_BULKY_INPUT_KEYS = ("content", "file_text", "new_string", "old_string")


def _cls(obj) -> str:
    return type(obj).__name__


def _trim(text, cap: int) -> str:
    text = "" if text is None else str(text)
    return text if len(text) <= cap else text[:cap] + f"… [+{len(text) - cap} chars]"


def summarize_tool_use(name: str, tool_input: dict) -> str:
    """A one-line, human-readable rendering of a tool call."""
    if not isinstance(tool_input, dict):
        return name
    if name == "Bash":
        return f"Bash: {_trim(tool_input.get('command', ''), 300)}"
    if name == "Skill":
        return f"Skill: {tool_input.get('name') or tool_input.get('skill') or ''}"
    for key in ("file_path", "path", "notebook_path"):
        if tool_input.get(key):
            return f"{name} {tool_input[key]}"
    if name in ("Grep", "Glob") and tool_input.get("pattern"):
        return f"{name} {tool_input['pattern']!r}"
    if name == "Task" and tool_input.get("description"):
        return f"Task: {tool_input['description']}"
    return name


def compact_tool_input(tool_input: dict) -> dict:
    """Strip file bodies out of a tool input before it is stored."""
    if not isinstance(tool_input, dict):
        return {}
    out = {}
    for key, value in tool_input.items():
        if key in _BULKY_INPUT_KEYS and isinstance(value, str):
            out[key] = {"_omitted_chars": len(value)}
        elif isinstance(value, str):
            out[key] = _trim(value, TOOL_INPUT_VALUE_CAP)
        else:
            out[key] = value
    return out


def _result_block_text(content) -> tuple[str, int]:
    if content is None:
        return "", 0
    if isinstance(content, str):
        return _trim(content, TOOL_RESULT_CAP), len(content)
    if isinstance(content, list):
        parts = [
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        ]
        joined = "\n".join(parts) if parts else str(content)
        return _trim(joined, TOOL_RESULT_CAP), len(joined)
    text = str(content)
    return _trim(text, TOOL_RESULT_CAP), len(text)


def sum_model_usage(model_usage) -> dict:
    """Total the camelCase per-model usage dict the CLI passes through."""
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
    }
    if not isinstance(model_usage, dict):
        return totals
    for usage in model_usage.values():
        if not isinstance(usage, dict):
            continue
        totals["input_tokens"] += int(usage.get("inputTokens") or 0)
        totals["output_tokens"] += int(usage.get("outputTokens") or 0)
        totals["cache_read_tokens"] += int(usage.get("cacheReadInputTokens") or 0)
        totals["cache_creation_tokens"] += int(
            usage.get("cacheCreationInputTokens") or 0
        )
    return totals


def record_message(message, recorder, state: dict) -> None:
    """Emit events for one SDK message and accumulate run-level state.

    ``state`` collects fields applied to the AgentRun once the stream ends:
    session_id, result fields, token totals and tool_use_counts.
    """
    kind = _cls(message)
    parent = getattr(message, "parent_tool_use_id", "") or ""

    if kind == "SystemMessage":
        subtype = getattr(message, "subtype", "") or ""
        data = getattr(message, "data", None) or {}
        if subtype == "init":
            session_id = data.get("session_id") or data.get("sessionId") or ""
            if session_id:
                state["session_id"] = session_id
            skills = data.get("skills") or []
            state["discovered_skills"] = skills
            recorder.emit(
                EventKind.INIT,
                f"Session started · model={data.get('model', '?')} · "
                f"{len(skills)} skill(s) discovered",
                data={
                    "skills": skills,
                    "slash_commands": data.get("slash_commands"),
                    "session_id": session_id,
                },
            )
        elif subtype == "compact_boundary":
            recorder.emit(EventKind.COMPACT, "Context compacted", data=data)
        elif subtype in NOISY_SYSTEM_SUBTYPES:
            # High-frequency bookkeeping. The first real run emitted 199
            # `thinking_tokens` rows out of 413 events — pure transcript noise.
            pass
        else:
            recorder.emit(EventKind.SYS, subtype or "system", data=data)
        return

    if kind == "AssistantMessage":
        for block in getattr(message, "content", None) or []:
            btype = _cls(block)
            if btype == "TextBlock":
                text = getattr(block, "text", "") or ""
                if text.strip():
                    recorder.emit(EventKind.ASSISTANT, text, parent_tool_use_id=parent)
            elif btype == "ThinkingBlock":
                recorder.emit(
                    EventKind.THINKING,
                    _trim(getattr(block, "thinking", "") or "", THINKING_CAP),
                    parent_tool_use_id=parent,
                )
            elif btype == "ToolUseBlock":
                name = getattr(block, "name", "") or ""
                tool_input = getattr(block, "input", None) or {}
                counts = state.setdefault("tool_use_counts", {})
                counts[name] = counts.get(name, 0) + 1
                recorder.emit(
                    EventKind.SKILL if name == "Skill" else EventKind.TOOL_USE,
                    summarize_tool_use(name, tool_input),
                    tool_name=name,
                    tool_use_id=getattr(block, "id", "") or "",
                    parent_tool_use_id=parent,
                    data=compact_tool_input(tool_input),
                )
                if name in ("Write", "Edit", "MultiEdit"):
                    for key in ("file_path", "path"):
                        if tool_input.get(key):
                            state.setdefault("touched_files", set()).add(
                                tool_input[key]
                            )
        return

    if kind == "UserMessage":
        content = getattr(message, "content", None)
        if isinstance(content, list):
            for block in content:
                if _cls(block) == "ToolResultBlock":
                    text, full_len = _result_block_text(getattr(block, "content", None))
                    is_error = bool(getattr(block, "is_error", False))
                    recorder.emit(
                        EventKind.TOOL_RESULT,
                        text,
                        level=EventLevel.ERR if is_error else EventLevel.INFO,
                        tool_use_id=getattr(block, "tool_use_id", "") or "",
                        parent_tool_use_id=parent,
                        is_error=is_error,
                        data={"is_error": is_error, "len": full_len},
                    )
        elif isinstance(content, str) and content.strip():
            recorder.emit(EventKind.USER, content, parent_tool_use_id=parent)
        return

    if kind == "ResultMessage":
        totals = sum_model_usage(getattr(message, "model_usage", None))
        state.update(totals)
        state["result_subtype"] = getattr(message, "subtype", "") or ""
        state["terminal_reason"] = getattr(message, "terminal_reason", "") or ""
        state["result_text"] = getattr(message, "result", "") or ""
        state["num_turns"] = getattr(message, "num_turns", None)
        state["duration_api_ms"] = getattr(message, "duration_api_ms", None)
        state["total_cost_usd"] = getattr(message, "total_cost_usd", None)
        state["api_error_status"] = getattr(message, "api_error_status", None)
        state["is_error"] = bool(getattr(message, "is_error", False))
        state["permission_denials"] = getattr(message, "permission_denials", None)
        if getattr(message, "session_id", ""):
            state["session_id"] = message.session_id

        cost = state.get("total_cost_usd")
        recorder.emit(
            EventKind.RESULT,
            f"Result: {state['result_subtype'] or 'done'} · "
            f"turns={state.get('num_turns')} · "
            f"cost=${cost if cost is not None else '?'} · "
            f"in={totals['input_tokens']}/out={totals['output_tokens']}",
            level=EventLevel.ERR if state["is_error"] else EventLevel.INFO,
            is_error=state["is_error"],
            data={
                "terminal_reason": state["terminal_reason"],
                "api_error_status": state["api_error_status"],
                **totals,
            },
        )
        return

    recorder.emit(EventKind.SYS, f"{kind}", data=None)
