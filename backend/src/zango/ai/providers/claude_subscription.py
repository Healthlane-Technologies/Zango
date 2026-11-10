"""
Claude on a subscription login, for local testing only.

The same switch as Build with AI: ``AGENT_MODE_AUTH=subscription`` with
``CLAUDE_CODE_OAUTH_TOKEN`` set and ``DEBUG`` on. Anywhere else this service is
hidden and its accounts report "not connected". The Messages API rejects a
subscription login, so each call is one turn through the Claude Code CLI
(``claude_agent_sdk``), as ``agent_mode.naming._complete_via_sdk`` does.

Tools: an agent's tools are offered to the CLI as an in-process MCP server whose
handlers do nothing, with ``max_turns=1``. The CLI streams one ``ToolUseBlock``
per call and stops at the turn limit; the provider returns them as
``stop_reason="tool_use"`` and Zango's own loop (``AgentClient`` and
``ToolExecutor``) runs and logs them, so no tool ever runs inside the CLI. (A
``can_use_tool`` deny with ``interrupt=True`` was tried first: it aborts the CLI
after the first call, losing parallel ones.) Earlier calls and results go back
to the CLI as text in the next prompt.

Limits (it is a testing aid, not a production route):
- files go to the CLI only as base64 image or document blocks (Files API ids and URLs
  are named, not sent);
- a JSON schema is asked for in the system prompt, not enforced;
- each call starts the CLI, so it takes a few seconds; cost is reported as 0.
"""

import json
import re
import time

from zango.ai.exceptions import LLMAPIError, LLMTimeoutError
from zango.ai.providers.anthropic import AnthropicProvider
from zango.ai.providers.base import (
    BaseLLMProvider,
    LLMResponse,
    LLMStreamChunk,
    LLMToolCall,
    LLMUsage,
)
from zango.ai.providers.registry import register_provider


SLUG = "claude_subscription"
UNAVAILABLE = (
    "The Claude subscription login is for local testing only: set "
    "AGENT_MODE_AUTH=subscription and CLAUDE_CODE_OAUTH_TOKEN, with DEBUG on."
)


def subscription_credentials():
    """The subscription credential, or None when the switch is off."""
    from django.conf import settings

    if not getattr(settings, "DEBUG", False):
        return None
    if getattr(settings, "AGENT_MODE_AUTH", "api_key") != "subscription":
        return None
    from zango.apps.agent_mode.credentials import resolve_credentials

    creds = resolve_credentials()
    return creds if creds.oauth_token else None


TOOL_SERVER = "zango"
TOOL_PREFIX = f"mcp__{TOOL_SERVER}__"


def _text(content, names=None) -> str:
    """Message content as text. ``names`` maps tool_use ids to tool names."""
    if isinstance(content, str):
        return content
    names = names if names is not None else {}
    out = []
    for block in content or []:
        if isinstance(block, dict):
            if block.get("type") in ("image", "document"):
                if (block.get("source") or {}).get(
                    "type"
                ) != "base64":  # base64 ones go as blocks
                    out.append(f"[attached {block['type']} not sent in local testing]")
            elif block.get("type") == "text":
                out.append(block.get("text") or "")
            elif block.get("type") == "tool_use":
                names[block.get("id")] = block.get("name")
                out.append(
                    f"[called tool {block.get('name')} with "
                    f"{json.dumps(block.get('input') or {})}]"
                )
            elif block.get("type") == "tool_result":
                name = names.get(block.get("tool_use_id")) or "tool"
                failed = " (failed)" if block.get("is_error") else ""
                out.append(
                    f"[result of tool {name}{failed}]\n{_text(block.get('content'), names)}"
                )
        else:
            out.append(str(block))
    return "\n".join(x for x in out if x)


def _attachments(messages) -> list:
    """The base64 image and document blocks of the user messages, to send beside the prompt."""
    out = []
    for m in messages:
        if m.role != "user" or not isinstance(m.content, list):
            continue
        for b in m.content:
            if (
                isinstance(b, dict)
                and b.get("type") in ("image", "document")
                and (b.get("source") or {}).get("type") == "base64"
            ):
                out.append(b)
    return out


def _prompt(messages) -> str:
    """The conversation as one prompt: the CLI takes a single user turn."""
    parts = []
    names = {}
    for m in messages:
        body = _text(m.content, names)
        for f in m.files or []:
            body = (
                f"[attached file not sent in local testing: {f.filename or f.media_type}]\n"
                + body
            )
        if not body:
            continue
        parts.append(body if m.role == "user" else f"[{m.role}]\n{body}")
    if len(parts) == 1:
        return parts[0]
    return "Conversation so far, oldest first:\n\n" + "\n\n".join(parts)


def _unfence(text: str) -> str:
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


@register_provider(SLUG, "Claude subscription (local testing)", icon="anthropic.svg")
class ClaudeSubscriptionProvider(BaseLLMProvider):
    # the CLI route offers tools (run by Zango, not the CLI) and base64 files
    supported_models = [
        {**m, "supports_tools": True, "supports_vision": True}
        for m in AnthropicProvider.supported_models
    ]
    config_fields = []

    @classmethod
    def available(cls) -> bool:
        return subscription_credentials() is not None

    def _run(
        self,
        prompt: str,
        model: str,
        system: str,
        timeout: float,
        tools=None,
        attachments=None,
    ):
        """One CLI turn: ``(text, usage, calls)``, calls being ``(id, name, input)``.
        ``attachments`` (image / document blocks) go in the same user turn as the prompt."""
        import asyncio
        import concurrent.futures

        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            ResultError,
            ResultMessage,
            SdkMcpTool,
            TextBlock,
            ToolUseBlock,
            create_sdk_mcp_server,
            query,
        )

        from zango.apps.agent_mode.options import agent_home, build_env

        creds = subscription_credentials()
        if creds is None:
            raise LLMAPIError(UNAVAILABLE)
        home = agent_home()

        async def nothing(args):
            # The CLI must never run a tool: Zango's ToolExecutor does, after
            # this turn. The turn limit stops the CLI before it reads this.
            return {"content": [{"type": "text", "text": "Handled by the host."}]}

        extra = {}
        if tools:
            extra = {
                "mcp_servers": {
                    TOOL_SERVER: create_sdk_mcp_server(
                        TOOL_SERVER,
                        tools=[
                            SdkMcpTool(
                                name=t.name,
                                description=t.description,
                                input_schema=t.input_schema,
                                handler=nothing,
                            )
                            for t in tools
                        ],
                    )
                },
                "allowed_tools": [TOOL_PREFIX + t.name for t in tools],
            }
        options = ClaudeAgentOptions(
            cwd=home,
            tools=[],  # the CLI's own tools (files, shell, web) stay off
            max_turns=1,
            setting_sources=[],
            model=model or None,
            system_prompt=system or None,
            env=build_env(creds, home),
            **extra,
        )

        async def turn():
            yield {
                "type": "user",
                "parent_tool_use_id": None,
                "session_id": "default",
                "message": {
                    "role": "user",
                    "content": [*attachments, {"type": "text", "text": prompt}],
                },
            }

        async def run():
            chunks, calls, usage = [], [], {}
            try:
                async for message in query(
                    prompt=turn() if attachments else prompt, options=options
                ):
                    if isinstance(message, AssistantMessage):
                        for b in message.content:
                            if isinstance(b, TextBlock):
                                chunks.append(b.text)
                            elif isinstance(b, ToolUseBlock):
                                calls.append(
                                    (
                                        b.id,
                                        b.name.removeprefix(TOOL_PREFIX),
                                        dict(b.input or {}),
                                    )
                                )
                    elif isinstance(message, ResultMessage):
                        usage = getattr(message, "usage", None) or {}
            except ResultError as exc:
                # A turn that asked for tools ends at the turn limit: expected.
                if not calls or exc.subtype != "error_max_turns":
                    raise
            return "".join(chunks), usage, calls

        async def bounded():
            return await asyncio.wait_for(run(), timeout)

        # A worker with a running event loop can't asyncio.run; use a thread.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(bounded())).result()

    def complete(
        self,
        messages,
        model,
        tools=None,
        temperature=1.0,
        max_tokens=4096,
        system=None,
        stop_sequences=None,
        **kwargs,
    ):
        system = system or ""
        fmt = kwargs.get("response_format")
        if isinstance(fmt, dict):
            system += (
                "\n\nReply with ONLY a JSON object matching this JSON schema, with no other "
                "text and no code fences:\n" + json.dumps(fmt)
            )
        elif fmt == "json":
            system += (
                "\n\nReply with ONLY valid JSON, with no other text and no code fences."
            )
        timeout = float(kwargs.get("timeout_seconds") or 120)

        start = time.monotonic()
        try:
            text, usage, calls = self._run(
                _prompt(messages),
                model,
                system.strip(),
                timeout,
                tools,
                _attachments(messages),
            )
        except TimeoutError as exc:
            raise LLMTimeoutError(
                f"The Claude CLI did not answer within {timeout:.0f}s"
            ) from exc
        except LLMAPIError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise LLMAPIError(f"Claude subscription call failed: {exc}") from exc
        if fmt and not calls:
            text = _unfence(text)
        return LLMResponse(
            content=text,
            tool_calls=[LLMToolCall(id=i, name=n, input=a) for i, n, a in calls],
            stop_reason="tool_use" if calls else "end_turn",
            usage=LLMUsage(
                input_tokens=int(usage.get("input_tokens") or 0),
                output_tokens=int(usage.get("output_tokens") or 0),
                cache_creation_tokens=int(
                    usage.get("cache_creation_input_tokens") or 0
                ),
                cache_read_tokens=int(usage.get("cache_read_input_tokens") or 0),
            ),
            model=model,
            raw_response=None,
            latency_ms=int((time.monotonic() - start) * 1000),
        )

    def stream(
        self,
        messages,
        model,
        tools=None,
        temperature=1.0,
        max_tokens=4096,
        system=None,
        stop_sequences=None,
        **kwargs,
    ):
        r = self.complete(
            messages,
            model,
            tools,
            temperature,
            max_tokens,
            system,
            stop_sequences,
            **kwargs,
        )
        if r.content:
            yield LLMStreamChunk(delta_text=r.content)
        yield LLMStreamChunk(is_final=True, usage=r.usage, stop_reason=r.stop_reason)

    def validate_config(self):
        # no network call: the login is checked by the CLI on first use
        return (True, None) if self.available() else (False, UNAVAILABLE)

    def get_models(self):
        return self.supported_models

    def compute_cost(self, usage, model):
        return 0.0  # billed to the subscription, not the API
