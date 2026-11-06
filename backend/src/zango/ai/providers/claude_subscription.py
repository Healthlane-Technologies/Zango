"""
Claude on a subscription login, for local testing only.

The same switch as Build with AI: ``AGENT_MODE_AUTH=subscription`` with
``CLAUDE_CODE_OAUTH_TOKEN`` set and ``DEBUG`` on. Anywhere else this service is
hidden and its accounts report "not connected". The Messages API rejects a
subscription login, so each call is one tool-less turn through the Claude Code
CLI (``claude_agent_sdk``), as ``agent_mode.naming._complete_via_sdk`` does.

Limits (it is a testing aid, not a production route):
- no tool calls: an agent's tools are not offered;
- files are not sent, only their names;
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


def _text(content) -> str:
    if isinstance(content, str):
        return content
    out = []
    for block in content or []:
        if isinstance(block, dict):
            if block.get("type") == "text":
                out.append(block.get("text") or "")
            elif block.get("type") == "tool_result":
                out.append(_text(block.get("content")))
        else:
            out.append(str(block))
    return "\n".join(x for x in out if x)


def _prompt(messages) -> str:
    """The conversation as one prompt: the CLI takes a single user turn."""
    parts = []
    for m in messages:
        body = _text(m.content)
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
    # the CLI route sends no tools and no files
    supported_models = [
        {**m, "supports_tools": False, "supports_vision": False}
        for m in AnthropicProvider.supported_models
    ]
    config_fields = []

    @classmethod
    def available(cls) -> bool:
        return subscription_credentials() is not None

    def _run(self, prompt: str, model: str, system: str, timeout: float):
        import asyncio
        import concurrent.futures

        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            ResultMessage,
            TextBlock,
            query,
        )

        from zango.apps.agent_mode.options import agent_home, build_env

        creds = subscription_credentials()
        if creds is None:
            raise LLMAPIError(UNAVAILABLE)
        home = agent_home()
        options = ClaudeAgentOptions(
            cwd=home,
            tools=[],
            max_turns=1,
            setting_sources=[],
            model=model or None,
            system_prompt=system or None,
            env=build_env(creds, home),
        )

        async def run():
            chunks, usage = [], {}
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    chunks.extend(
                        b.text for b in message.content if isinstance(b, TextBlock)
                    )
                elif isinstance(message, ResultMessage):
                    usage = getattr(message, "usage", None) or {}
            return "".join(chunks), usage

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
            text, usage = self._run(_prompt(messages), model, system.strip(), timeout)
        except TimeoutError as exc:
            raise LLMTimeoutError(
                f"The Claude CLI did not answer within {timeout:.0f}s"
            ) from exc
        except LLMAPIError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise LLMAPIError(f"Claude subscription call failed: {exc}") from exc
        if fmt:
            text = _unfence(text)
        return LLMResponse(
            content=text,
            tool_calls=[],
            stop_reason="end_turn",
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
