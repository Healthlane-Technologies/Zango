"""
ProviderClient wraps a BaseLLMProvider instance with framework concerns:
- Automatic invocation logging
- Cost computation and budget tracking
- Rate limit checking
- Error type normalization

App developers interact with this, not the raw provider.
"""

import logging
import time

from dataclasses import asdict
from typing import Iterator, Optional

from zango.ai.exceptions import (
    BudgetExceeded,
    LLMAPIError,
    LLMTimeoutError,
    ModelNotAvailable,
    RateLimitExceeded,
    ZangoAIError,
)
from zango.ai.providers.base import LLMMessage, LLMResponse, LLMStreamChunk, LLMToolDef


logger = logging.getLogger("zango.ai")


class ProviderClient:
    """
    Wrapper around a BaseLLMProvider instance that adds framework concerns.
    """

    def __init__(self, app_provider):
        """
        Args:
            app_provider: AppLLMProvider model instance
        """
        self._app_provider = app_provider
        self._raw_client = None

    def _get_client(self):
        """Lazy-initialize the raw provider client."""
        if self._raw_client is None:
            self._raw_client = self._app_provider.get_client()
        return self._raw_client

    def _resolve_model(self, model: Optional[str]) -> str:
        """Resolve model: use default if not specified."""
        if model:
            return model
        return self._app_provider.default_model

    def _check_model_enabled(self, model: str):
        """Check if the requested model is enabled for this provider."""
        enabled = self._app_provider.enabled_models.filter(
            model_id=model, is_enabled=True
        )
        if enabled.exists():
            return
        # If no enabled_models records exist at all, allow any model
        # (provider was set up before model tracking)
        if not self._app_provider.enabled_models.exists():
            return
        raise ModelNotAvailable(model, self._app_provider.name)

    def _serialize_messages(self, messages):
        """Convert messages list to JSON-serializable format for logging."""
        result = []
        for msg in messages:
            if isinstance(msg, LLMMessage):
                entry = {"role": msg.role, "content": msg.content}
                if msg.tool_calls:
                    entry["tool_calls"] = msg.tool_calls
                if msg.tool_call_id:
                    entry["tool_call_id"] = msg.tool_call_id
                result.append(entry)
            elif isinstance(msg, dict):
                result.append(msg)
            else:
                result.append(str(msg))
        return result

    def _extract_file_metadata(self, messages):
        """Extract file metadata (filename, media_type, size_bytes) from messages for logging."""
        files_meta = []
        for msg in messages:
            if not isinstance(msg, LLMMessage) or not msg.files:
                continue
            for f in msg.files:
                meta = {
                    "filename": f.filename or None,
                    "media_type": f.media_type or None,
                    "size_bytes": len(f.data) if f.data else None,
                    "source": "url" if f.url else "upload",
                }
                if f.url:
                    meta["url"] = f.url
                files_meta.append(meta)
        return files_meta or None

    def _serialize_tools(self, tools):
        """Convert tools list to JSON-serializable format for logging."""
        if not tools:
            return None
        result = []
        for tool in tools:
            if isinstance(tool, LLMToolDef):
                result.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                    }
                )
            elif isinstance(tool, dict):
                result.append(tool)
        return result

    def _log_invocation(
        self,
        model,
        messages,
        system,
        tools,
        params,
        response=None,
        error=None,
        status="success",
        latency_ms=None,
        cost_usd=0,
        triggered_by="user",
        agent=None,
        agent_name="",
        system_prompt_name="",
        system_prompt_version=None,
        user_prompt_name="",
        user_prompt_version=None,
        rendered_system_prompt=None,
        context_snapshot=None,
        run_id=None,
        round_number=None,
        session_id=None,
        request_files_meta=None,
    ):
        """Create an AppLLMInvocation log entry."""
        from zango.apps.ai.models import AppLLMInvocation

        invocation_data = {
            "provider": self._app_provider,
            "provider_name": self._app_provider.name,
            "provider_slug": self._app_provider.provider_slug,
            "model": model,
            "request_messages": self._serialize_messages(messages),
            "request_system": system,
            "request_tools": self._serialize_tools(tools),
            "request_params": params,
            "request_files": request_files_meta
            if request_files_meta is not None
            else self._extract_file_metadata(messages),
            "status": status,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "triggered_by": triggered_by,
            "agent": agent,
            "agent_name": agent_name or "",
            "system_prompt_name": system_prompt_name or "",
            "system_prompt_version": system_prompt_version,
            "user_prompt_name": user_prompt_name or "",
            "user_prompt_version": user_prompt_version,
            "rendered_system_prompt": rendered_system_prompt,
            "context_snapshot": context_snapshot,
            "run_id": run_id,
            "round_number": round_number,
            "session_id": session_id,
        }

        if response:
            invocation_data["response_content"] = response.content
            invocation_data["response_tool_calls"] = (
                [asdict(tc) for tc in response.tool_calls]
                if response.tool_calls
                else None
            )
            invocation_data["stop_reason"] = response.stop_reason
            invocation_data["input_tokens"] = response.usage.input_tokens
            invocation_data["output_tokens"] = response.usage.output_tokens
            invocation_data["cache_creation_tokens"] = (
                response.usage.cache_creation_tokens
            )
            invocation_data["cache_read_tokens"] = response.usage.cache_read_tokens
            invocation_data["time_to_first_token_ms"] = response.time_to_first_token_ms

        if error:
            invocation_data["error_message"] = str(error)
            invocation_data["error_type"] = type(error).__name__

        try:
            invocation = AppLLMInvocation.objects.create(**invocation_data)
            return invocation
        except Exception as log_err:
            logger.error(f"Failed to log AI invocation: {log_err}")
            return None

    def _extract_agent_kwargs(self, kwargs):
        """Extract agent/prompt tracking fields from kwargs, returning (agent_kwargs, remaining_kwargs)."""
        agent_fields = [
            "agent",
            "agent_name",
            "system_prompt_name",
            "system_prompt_version",
            "user_prompt_name",
            "user_prompt_version",
            "rendered_system_prompt",
            "context_snapshot",
            "run_id",
            "round_number",
            "session_id",
            "request_files_meta",
        ]
        agent_kwargs = {k: kwargs.pop(k) for k in agent_fields if k in kwargs}
        return agent_kwargs

    def _extract_timeout(self, kwargs):
        """Pop and return timeout_seconds from kwargs (default None = provider default)."""
        return kwargs.pop("timeout_seconds", None)

    def complete(
        self,
        messages: list[LLMMessage],
        model: str = None,
        tools: Optional[list[LLMToolDef]] = None,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        stop_sequences: Optional[list[str]] = None,
        triggered_by: str = "user",
        **kwargs,
    ) -> LLMResponse:
        """
        Synchronous completion with automatic logging, cost tracking, and budget enforcement.
        """
        # Extract agent tracking kwargs before passing rest to provider
        agent_kwargs = self._extract_agent_kwargs(kwargs)
        timeout_seconds = self._extract_timeout(kwargs)

        model = self._resolve_model(model)
        self._check_model_enabled(model)
        client = self._get_client()

        params = {
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stop_sequences:
            params["stop_sequences"] = stop_sequences

        provider_kwargs = dict(kwargs)
        if timeout_seconds is not None:
            provider_kwargs["timeout_seconds"] = timeout_seconds

        try:
            response = client.complete(
                messages=messages,
                model=model,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system,
                stop_sequences=stop_sequences,
                **provider_kwargs,
            )

            # Compute cost
            cost = client.compute_cost(response.usage, model)
            response.cost_usd = cost

            # Log invocation
            invocation = self._log_invocation(
                model=model,
                messages=messages,
                system=system,
                tools=tools,
                params=params,
                response=response,
                cost_usd=cost,
                latency_ms=response.latency_ms,
                triggered_by=triggered_by,
                **agent_kwargs,
            )
            if invocation:
                response.invocation_id = invocation.pk

            # Update provider usage counters
            self._app_provider.record_usage(response.usage, cost)

            return response

        except ZangoAIError as e:
            error_status = "error"
            if isinstance(e, RateLimitExceeded):
                error_status = "rate_limited"
            elif isinstance(e, LLMTimeoutError):
                error_status = "timeout"
            elif isinstance(e, BudgetExceeded):
                error_status = "budget_exceeded"

            self._log_invocation(
                model=model,
                messages=messages,
                system=system,
                tools=tools,
                params=params,
                error=e,
                status=error_status,
                triggered_by=triggered_by,
                **agent_kwargs,
            )
            raise

        except Exception as e:
            self._log_invocation(
                model=model,
                messages=messages,
                system=system,
                tools=tools,
                params=params,
                error=e,
                status="error",
                triggered_by=triggered_by,
                **agent_kwargs,
            )
            raise LLMAPIError(str(e), original_error=e) from e

    def stream(
        self,
        messages: list[LLMMessage],
        model: str = None,
        tools: Optional[list[LLMToolDef]] = None,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        stop_sequences: Optional[list[str]] = None,
        triggered_by: str = "user",
        **kwargs,
    ) -> Iterator[LLMStreamChunk]:
        """
        Streaming completion. Logs on stream completion (final chunk).
        """
        model = self._resolve_model(model)
        self._check_model_enabled(model)
        client = self._get_client()

        params = {
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start = time.monotonic()
        accumulated_text = []
        final_usage = None
        final_stop_reason = None

        try:
            for chunk in client.stream(
                messages=messages,
                model=model,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                system=system,
                stop_sequences=stop_sequences,
                **kwargs,
            ):
                if chunk.delta_text:
                    accumulated_text.append(chunk.delta_text)

                if chunk.is_final and chunk.usage:
                    final_usage = chunk.usage
                    final_stop_reason = chunk.stop_reason

                yield chunk

            # After stream completes, log the invocation
            latency_ms = int((time.monotonic() - start) * 1000)
            cost = 0
            if final_usage:
                cost = client.compute_cost(final_usage, model)
                self._app_provider.record_usage(final_usage, cost)

            from zango.ai.providers.base import LLMResponse, LLMUsage

            # Create a minimal response for logging
            log_response = LLMResponse(
                content="".join(accumulated_text),
                tool_calls=[],
                stop_reason=final_stop_reason or "end_turn",
                usage=final_usage or LLMUsage(input_tokens=0, output_tokens=0),
                model=model,
                raw_response=None,
                latency_ms=latency_ms,
            )

            self._log_invocation(
                model=model,
                messages=messages,
                system=system,
                tools=tools,
                params=params,
                response=log_response,
                cost_usd=cost,
                latency_ms=latency_ms,
                triggered_by=triggered_by,
            )

        except ZangoAIError as e:
            self._log_invocation(
                model=model,
                messages=messages,
                system=system,
                tools=tools,
                params=params,
                error=e,
                status="error",
                triggered_by=triggered_by,
            )
            raise

    def complete_async(
        self,
        messages: list[LLMMessage],
        model: str = None,
        tools: Optional[list[LLMToolDef]] = None,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        triggered_by: str = "celery",
        **kwargs,
    ) -> str:
        """
        Dispatches completion to a Celery task. Returns task_id.
        The Celery task calls complete() synchronously.
        """
        from zango.ai.tasks import async_llm_complete

        model = self._resolve_model(model)

        # Serialize messages for Celery
        serialized_messages = self._serialize_messages(messages)
        serialized_tools = self._serialize_tools(tools)

        task = async_llm_complete.delay(
            provider_name=self._app_provider.name,
            messages=serialized_messages,
            model=model,
            tools=serialized_tools,
            temperature=temperature,
            max_tokens=max_tokens,
            system=system,
            triggered_by=triggered_by,
            **kwargs,
        )
        return task.id
