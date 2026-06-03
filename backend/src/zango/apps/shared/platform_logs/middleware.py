"""Bind the stdout proxy for the duration of every Django request.

Mirrors `celery_print_capture.py` for the gunicorn / web worker side.
A `print()` inside a view, model method, signal receiver, or any helper
called during the request lifecycle is forwarded as an `INFO` log
record under the `zango.request.stdout` logger — which propagates to
the root logger and picks up the verbose formatter + tenant_filter.

Thread- and async-safe via ContextVar — see `stdout_proxy` docstring.
"""

from __future__ import annotations

from zango.apps.shared.platform_logs import stdout_proxy


class RequestPrintCaptureMiddleware:
    """Wrap every request with a stdout-proxy binding so `print()` calls
    become tenant-tagged log records.

    Install near the top of `MIDDLEWARE` — before any middleware whose
    own `print()` / log calls you want captured. After SecurityMiddleware
    is fine; placing it as the very first entry is also safe.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bind each stream to its own logger via stream-specific
        # ContextVars. Using one shared ContextVar would let the second
        # bind() clobber the first — every stdout write would then be
        # logged under the stderr logger name.
        stdout_token = stdout_proxy.bind_stdout("zango.request.stdout")
        try:
            stderr_token = stdout_proxy.bind_stderr("zango.request.stderr")
        except Exception:
            stdout_proxy.reset_stdout(stdout_token)
            raise
        try:
            return self.get_response(request)
        finally:
            # LIFO of bind order: stderr first, stdout last. Wrap each
            # reset in its own try/finally so a failure resetting stderr
            # (or anything that writes to stderr during teardown) still
            # leaves stdout cleared.
            try:
                stdout_proxy.reset_stderr(stderr_token)
            finally:
                stdout_proxy.reset_stdout(stdout_token)
