"""Celery task that runs Code Execution snippets.

Composes all four isolation layers and the codexec helper:
- L1: AST recheck on the source snapshot at pickup time.
- L2: SET LOCAL ROLE inside an atomic() block (Postgres-level isolation).
- L3: SET LOCAL search_path + statement_timeout.
- L4: ConnectionGuard for reflective tenant-switching attempts.

Captures stdout/stderr (Phase 1) into the CodeExecution row. Updates status,
duration, return value, traceback. Outputs written via codexec.write(...) are
preserved even when the user code raises — exceptions are caught inside the
transaction so the surrounding writes commit.
"""

from __future__ import annotations

import json
import logging
import sys
import time
import traceback
from typing import Any, Optional

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from django.db import connection, transaction
from django.utils import timezone

from zango import codexec
from zango.apps.code_execution.guard import install_connection_guard
from zango.apps.code_execution.isolation import begin_isolated_session
from zango.apps.code_execution.models import (
    CodeExecution,
    CodeExecutionLogLine,
    ExecStatus,
    LogLevel,
)
from zango.apps.code_execution.validator import validate
from zango.apps.dynamic_models.workspace.base import Workspace
from zango.apps.shared.tenancy.models import TenantModel


log = logging.getLogger(__name__)


# Caps per spec
STDOUT_CAP_BYTES = 1 * 1024 * 1024   # 1 MB
STDERR_CAP_BYTES = 256 * 1024        # 256 KB
LINE_CAP_BYTES = 8 * 1024            # 8 KB
RETURN_VALUE_CAP_BYTES = 64 * 1024   # 64 KB


# ---------------------------------------------------------------------------
# Stream capture
# ---------------------------------------------------------------------------


# Noisy library loggers we never want flooding the live tail.
# Their internal DEBUG/INFO would otherwise drown out user output and, worse,
# can spawn DB inserts from worker threads that aren't in the tenant schema.
_NOISY_LOGGER_PREFIXES = (
    "botocore",
    "boto3",
    "s3transfer",
    "urllib3",
    "asyncio",
    "django.db.backends",
    "PIL",
)


class _NoisyLoggerFilter(logging.Filter):
    """Drops records from known-noisy 3rd-party libraries."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        return not any(record.name.startswith(p) for p in _NOISY_LOGGER_PREFIXES)


class _CodexecLogHandler(logging.Handler):
    """Stdlib logging handler that feeds records into the LineLogger.

    Mounted on the root logger for the run's duration so user code that calls
    `logging.info(...)` / a library's logger ends up in the live tail.

    Hardened so that failure to persist a log line never raises back into the
    logging system — that would cause infinite recursion when the failure
    itself triggers more logging.
    """

    LEVEL_MAP = {
        "DEBUG": "sys",
        "INFO": "info",
        "WARNING": "warn",
        "ERROR": "err",
        "CRITICAL": "err",
    }

    def __init__(self, line_logger: "LineLogger"):
        super().__init__()
        self.line_logger = line_logger

    def emit(self, record: logging.LogRecord) -> None:
        # Re-entry guard: if we're already inside a flush, skip so we don't
        # cascade into a recursion when the flush itself logs an error.
        if getattr(self.line_logger, "_flushing", False):
            return
        try:
            msg = self.format(record)
        except Exception:  # noqa: BLE001
            try:
                msg = record.getMessage()
            except Exception:  # noqa: BLE001
                return
        level = self.LEVEL_MAP.get(record.levelname.upper(), "info")
        try:
            self.line_logger.emit(level, msg)
        except Exception:  # noqa: BLE001
            # Never propagate errors out of a logging path.
            return


class LineLogger:
    """Shared per-line buffer that also fans out into the CodeExecutionLogLine table.

    Each stream (stdout / stderr / SYS) shares the same logger so the `seq`
    field stays monotonic across the whole run. Lines are buffered and
    flushed in small batches via Django's ORM. Because the executor no longer
    wraps the run in an outer `transaction.atomic()`, each flush is
    autocommitted and immediately visible to the log-tail endpoint.
    """

    BATCH_SIZE = 16

    def __init__(self, execution_pk: int):
        self.execution_pk = execution_pk
        self._seq = 0
        self._pending: list[CodeExecutionLogLine] = []
        # Re-entry guard — set while flushing so the stdlib handler skips
        # records emitted by the flush itself (avoids infinite recursion).
        self._flushing = False

    def emit(self, level: str, message: str) -> None:
        if not message:
            return
        # Strip trailing newline so the DB stores clean lines.
        if message.endswith("\n"):
            message = message[:-1]
        if not message:
            return
        # Cap per-line size; oversized lines are clipped with a marker.
        if len(message) > LINE_CAP_BYTES:
            message = message[:LINE_CAP_BYTES] + "… [line truncated]"
        self._seq += 1
        self._pending.append(
            CodeExecutionLogLine(
                execution_id=self.execution_pk,
                seq=self._seq,
                level=level,
                message=message,
            )
        )
        if len(self._pending) >= self.BATCH_SIZE:
            self.flush()

    def emit_lines(self, level: str, blob: str) -> None:
        # Split arbitrarily-buffered data into discrete lines.
        if not blob:
            return
        # Keep trailing partials as a single line for now (no streaming logic in v1).
        for line in blob.splitlines():
            self.emit(level, line)

    def flush(self) -> None:
        if not self._pending:
            return
        # Set flushing flag so stdlib handler skips re-entry while we work.
        self._flushing = True
        try:
            try:
                CodeExecutionLogLine.objects.bulk_create(self._pending)
            except Exception:  # noqa: BLE001
                # Never raise from a logging path — that triggers more logging
                # and can cascade into infinite recursion. Drop the batch silently.
                pass
            finally:
                self._pending = []
        finally:
            self._flushing = False


class CapturingStream:
    """File-like that buffers writes up to `max_bytes`, then drops silently.

    In Phase 2 it also fans every line out to the LineLogger so the live
    tail can stream incremental updates.
    """

    def __init__(
        self,
        max_bytes: int,
        label: str,
        level: str,
        line_logger: "LineLogger",
    ):
        self.max_bytes = max_bytes
        self.label = label
        self.level = level
        self.line_logger = line_logger
        self._chunks: list[str] = []
        self._size = 0
        self._truncated = False
        self._line_buf = ""

    # File-like protocol -------------------------------------------------

    def write(self, data) -> int:
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        elif not isinstance(data, str):
            data = str(data)

        if self._truncated:
            return len(data)

        # Per-line cap (very long lines are clipped with marker).
        if "\n" not in data and len(data) > LINE_CAP_BYTES:
            data = data[:LINE_CAP_BYTES] + "… [line truncated]\n"

        remaining = self.max_bytes - self._size
        if len(data) > remaining:
            if remaining > 0:
                self._chunks.append(data[:remaining])
                self._size += remaining
            self._chunks.append(
                f"\n--- {self.label} truncated at {self.max_bytes} bytes ---\n"
            )
            self._truncated = True
        else:
            self._chunks.append(data)
            self._size += len(data)

        # Line-emit logic: accumulate partial line, flush on newline.
        self._line_buf += data
        while "\n" in self._line_buf:
            line, self._line_buf = self._line_buf.split("\n", 1)
            self.line_logger.emit(self.level, line)
        return len(data)

    def writelines(self, lines) -> None:
        for line in lines:
            self.write(line)

    def flush(self) -> None:
        # Flush any tail without a trailing newline so it shows in the live tail.
        if self._line_buf:
            self.line_logger.emit(self.level, self._line_buf)
            self._line_buf = ""

    def isatty(self) -> bool:
        return False

    def getvalue(self) -> str:
        return "".join(self._chunks)


# ---------------------------------------------------------------------------
# Return-value serialization
# ---------------------------------------------------------------------------


def _serialize_return(value: Any) -> tuple[Optional[Any], bool, str]:
    """Return (json-safe value, truncated_flag, error)."""
    if value is None:
        return None, False, ""
    try:
        payload = json.dumps(value, default=str, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        return (
            {"_error": "return value not JSON-serializable", "type": type(value).__name__},
            False,
            str(exc),
        )
    if len(payload.encode("utf-8")) > RETURN_VALUE_CAP_BYTES:
        return ({"_truncated": True, "preview": payload[:1024]}, True, "")
    return json.loads(payload), False, ""


def _alias_workspace_models_in_sys_modules(workspace) -> None:
    """Make `from workspaces.<tenant>.<path>.models import X` inside a
    codexec snippet return the SAME class object that pluginbase loaded
    during `Workspace.ready()`.

    Background:
    Workspace models are loaded twice in the same Python process under
    different namespaces — pluginbase's private internal_space (which is
    where Django, signals, and FKs get registered) and Python's regular
    import machinery (which a snippet's `from workspaces…import X`
    triggers). Same source file, two distinct class objects in memory.

    The mismatch surfaces whenever Django does an instance-type check
    against an FK target — most commonly during cascade collection on
    `.delete()`, where the user's direct-import instance is rejected
    because it's not an instance of the pluginbase class the FK was
    registered against:

        ValueError: Cannot query "WorkflowTransaction object (12555)":
                    Must be "WorkflowTransaction" instance.

    Fix: pre-populate sys.modules with the pluginbase-loaded module
    object under the direct-import path. Python's import machinery
    checks sys.modules before walking the filesystem, so the snippet's
    `from workspaces.<tenant>.<path>.models import X` short-circuits to
    the pluginbase module — and X is the registered class object.

    This only aliases modules that `workspace.get_models()` returns
    (i.e. workspace-defined models.py files). Non-model modules continue
    to load normally and aren't affected.
    """
    for module_path in workspace.get_models():
        # module_path looks like 'workspaces.<tenant>.<package_or_module>.models'
        split = module_path.split(".")
        if len(split) < 3 or split[0] != "workspaces":
            continue
        # Pluginbase relative path drops the 'workspaces.<tenant>.' prefix
        # to match what Workspace.load_models() passes to load_plugin().
        plugin_relative = ".".join(split[2:])
        try:
            pb_module = workspace.plugin_source.load_plugin(plugin_relative)
        except Exception:  # noqa: BLE001
            log.debug(
                "codexec: could not load %s via pluginbase for sys.modules alias",
                plugin_relative,
            )
            continue
        sys.modules[module_path] = pb_module


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------


@shared_task(bind=True, name="zango.code_execution.codexec_executor")
def codexec_executor(self, execution_uuid: str, tenant_name: str) -> dict:
    """Run a single CodeExecution row's snapshotted source.

    `execution_uuid` is the public object_uuid (stable across PK changes);
    we look up by that, then use the BigInt pk internally for FK joins.
    """
    started_at = timezone.now()
    started_perf = time.perf_counter()

    # 1. Bind tenant context
    tenant = TenantModel.objects.get(name=tenant_name)
    connection.set_tenant(tenant)

    # 2. Load row + mark running
    try:
        execution = CodeExecution.objects.select_related("snippet").get(
            object_uuid=execution_uuid
        )
    except CodeExecution.DoesNotExist:
        log.error("codexec: execution %s not found", execution_uuid)
        return {"status": "error", "reason": "execution_not_found"}

    # 2b. Framework-level suspend guard. Codexec has its own Celery task
    # that doesn't route through `zango_task_executor`, so the assertion
    # is repeated here. Catches the case where a run was enqueued before
    # the tenant was suspended and the flip happened while the task
    # waited in the queue. Order matters: we load the execution row first
    # so we can mark it ABORTED — otherwise the row stays at QUEUED
    # forever and the UI never learns the run was skipped.
    if getattr(tenant, "status", None) == "suspended":
        log.info(
            "codexec: skipping execution %s — tenant '%s' is suspended",
            execution_uuid,
            tenant.name,
        )
        execution.status = ExecStatus.ABORTED
        execution.exception_type = "TenantSuspended"
        execution.exception_message = (
            f"Tenant '{tenant.name}' is suspended. Run was skipped without "
            f"executing user code. Unsuspend the app and re-run to try again."
        )
        execution.ended_at = timezone.now()
        execution.duration_ms = int(
            (time.perf_counter() - started_perf) * 1000
        )
        execution.save(
            update_fields=[
                "status",
                "exception_type",
                "exception_message",
                "ended_at",
                "duration_ms",
                "modified_at",
            ]
        )
        return {"status": "skipped", "reason": "tenant_suspended"}

    execution.status = ExecStatus.RUNNING
    execution.started_at = started_at
    execution.celery_task_id = (self.request.id or "")[:64]
    execution.save(
        update_fields=["status", "started_at", "celery_task_id", "modified_at"]
    )

    # 3. Workspace context (sys.path patched, modules importable)
    try:
        ws = Workspace(connection.tenant, request=None, as_systemuser=True)
        ws.ready()
    except Exception as exc:  # noqa: BLE001
        return _finalize_error(
            execution,
            ExecStatus.FAILED,
            "WorkspaceLoadError",
            str(exc),
            traceback.format_exc(),
            started_perf,
        )

    # 3b. Make `from workspaces.<tenant>…import X` in the snippet resolve
    #     to the pluginbase-loaded class objects (the ones Django + signals
    #     + FKs are registered against). Without this, snippets that take
    #     the direct-import path hit class-identity mismatches on `.delete()`
    #     cascades and instance-based FK queries. See helper docstring.
    _alias_workspace_models_in_sys_modules(ws)

    # 4. AST recheck (L1) — catches deny-list updates between save and pickup
    violations = validate(execution.source_snapshot)
    if violations:
        message = "; ".join(f"L{v.line}: {v.message}" for v in violations[:5])
        return _finalize_error(
            execution,
            ExecStatus.FAILED,
            "CodeValidationError",
            message,
            "",
            started_perf,
        )

    # 5. Set up streams + line logger (shared monotonic seq across stdout/stderr/sys)
    line_logger = LineLogger(execution.id)
    line_logger.emit(LogLevel.SYS, f"Run picked up · celery_task_id={self.request.id}")
    line_logger.emit(LogLevel.SYS, f"Workspace ready · tenant={tenant_name}")
    line_logger.emit(LogLevel.SYS, "AST recheck OK · 0 violations")
    line_logger.flush()
    stdout = CapturingStream(STDOUT_CAP_BYTES, "stdout", LogLevel.OUT, line_logger)
    stderr = CapturingStream(STDERR_CAP_BYTES, "stderr", LogLevel.ERR, line_logger)
    saved_stdout, saved_stderr = sys.stdout, sys.stderr

    # 6. Pre-build the namespace for exec
    namespace: dict = {
        "__name__": "__codexec__",
        "__file__": "<codexec>",
        "__builtins__": __builtins__,
        "codexec": codexec,
    }

    status = ExecStatus.SUCCESS
    return_value: Any = None
    exc_type = exc_msg = exc_tb = ""

    # Install stdlib-logging + loguru bridges so any logger call lands in the
    # live tail too (not just print()). We restore originals in the `finally`.
    stdlib_handler = _CodexecLogHandler(line_logger)
    stdlib_handler.setFormatter(logging.Formatter("%(name)s · %(message)s"))
    stdlib_handler.addFilter(_NoisyLoggerFilter())
    # INFO is the right floor: DEBUG produces a flood of boto3/django internals;
    # INFO is what a user typically wants when they call `logging.info(...)`.
    stdlib_handler.setLevel(logging.INFO)
    root_logger = logging.getLogger()
    prev_root_level = root_logger.level
    root_logger.addHandler(stdlib_handler)
    if root_logger.level == logging.NOTSET or root_logger.level > logging.INFO:
        root_logger.setLevel(logging.INFO)

    loguru_sink_id = None
    _loguru_logger = None
    try:
        from loguru import logger as _loguru_logger  # type: ignore

        loguru_sink_id = _loguru_logger.add(
            lambda message: line_logger.emit(
                _CodexecLogHandler.LEVEL_MAP.get(
                    message.record["level"].name.upper(), "info"
                ),
                message.record["message"],
            ),
            format="{message}",
            level="DEBUG",
            colorize=False,
        )
    except ImportError:
        pass

    sys.stdout, sys.stderr = stdout, stderr
    try:
        # Atomic only around the exec call: gives SET LOCAL clean
        # transactional semantics, and any DB changes the user's code makes
        # are an atomic unit (rolled back if exec raises).
        with transaction.atomic():
            with connection.cursor() as c:
                begin_isolated_session(
                    c, tenant.schema_name, execution.snippet.timeout_seconds
                )
            with install_connection_guard():
                with codexec.bind_execution(str(execution.id)):
                    try:
                        code_obj = compile(
                            execution.source_snapshot, "<codexec>", "exec"
                        )
                        exec(code_obj, namespace)
                        return_value = namespace.get("codexec_result")
                    except SoftTimeLimitExceeded:
                        status = ExecStatus.TIMEOUT
                        exc_type = "TimeoutError"
                        exc_msg = (
                            f"Wall-clock timeout of "
                            f"{execution.snippet.timeout_seconds}s exceeded"
                        )
                        exc_tb = traceback.format_exc()
                    except BaseException as e:  # noqa: BLE001 - keep outputs on any error
                        status = ExecStatus.FAILED
                        exc_type = type(e).__name__[:128]
                        exc_msg = str(e)[:2048]
                        exc_tb = traceback.format_exc()
            # Atomic exits cleanly — codexec.write() and log line rows commit.
    finally:
        # Flush any trailing partial line + remaining batch before reverting streams.
        stdout.flush()
        stderr.flush()
        if exc_type:
            line_logger.emit(LogLevel.ERR, f"{exc_type}: {exc_msg.splitlines()[0] if exc_msg else ''}")
        line_logger.emit(LogLevel.SYS, f"Run ended · status={status}")
        line_logger.flush()
        sys.stdout, sys.stderr = saved_stdout, saved_stderr

        # Tear down logging bridges.
        try:
            root_logger.removeHandler(stdlib_handler)
            root_logger.setLevel(prev_root_level)
        except Exception:  # noqa: BLE001
            pass
        if loguru_sink_id is not None and _loguru_logger is not None:
            try:
                _loguru_logger.remove(loguru_sink_id)
            except Exception:  # noqa: BLE001
                pass

    # 7. Persist final state
    duration_ms = int((time.perf_counter() - started_perf) * 1000)
    rv, truncated, _ = _serialize_return(return_value)

    execution.status = status
    execution.ended_at = timezone.now()
    execution.duration_ms = duration_ms
    execution.stdout = stdout.getvalue()[:STDOUT_CAP_BYTES]
    execution.stderr = stderr.getvalue()[:STDERR_CAP_BYTES]
    execution.return_value = rv
    execution.return_value_truncated = truncated
    execution.exception_type = exc_type
    execution.exception_message = exc_msg
    execution.exception_traceback = exc_tb
    execution.save()

    log.info(
        "codexec: run %s %s in %dms (snippet=%s tenant=%s)",
        execution.id,
        status,
        duration_ms,
        execution.snippet_id,
        tenant_name,
    )
    return {"status": status, "duration_ms": duration_ms}


def _finalize_error(
    execution: CodeExecution,
    status: str,
    exc_type: str,
    exc_msg: str,
    exc_tb: str,
    started_perf: float,
) -> dict:
    """Persist an early-failure outcome (validation, workspace, etc.)."""
    execution.status = status
    execution.ended_at = timezone.now()
    execution.duration_ms = int((time.perf_counter() - started_perf) * 1000)
    execution.exception_type = exc_type[:128]
    execution.exception_message = exc_msg[:2048]
    execution.exception_traceback = exc_tb
    execution.save()
    return {"status": status, "exception_type": exc_type}


# ---------------------------------------------------------------------------
# Beat-scheduled sweeper for stuck runs
# ---------------------------------------------------------------------------


@shared_task(name="zango.code_execution.sweep_stuck_runs")
def sweep_stuck_runs() -> dict:
    """Mark executions stuck in `running` past their soft+hard budget as failed.

    Runs hourly (or whenever the beat schedule fires it). Looks at the
    snippet's timeout_seconds plus a generous grace window. If the worker
    died, the row sits as `running` forever otherwise.
    """
    from datetime import timedelta

    from zango.apps.shared.tenancy.models import TenantModel

    grace_factor = 2  # 2× the snippet timeout before we consider it lost
    swept_total = 0
    per_tenant: dict[str, int] = {}

    for tenant in TenantModel.objects.exclude(schema_name="public"):
        try:
            connection.set_tenant(tenant)
        except Exception:  # noqa: BLE001
            continue
        now = timezone.now()
        # Cheap heuristic: anything still 'running' for more than 2× the longest
        # plausible timeout window (max 300s → 600s grace).
        cutoff = now - timedelta(seconds=300 * grace_factor + 60)
        stuck = CodeExecution.objects.filter(
            status=ExecStatus.RUNNING, started_at__lt=cutoff
        )
        n = 0
        for ex in stuck:
            ex.status = ExecStatus.FAILED
            ex.exception_type = "WorkerLost"
            ex.exception_message = (
                "Heartbeat sweeper: no completion within 2× the timeout budget."
            )
            ex.ended_at = now
            if ex.started_at:
                ex.duration_ms = int((now - ex.started_at).total_seconds() * 1000)
            ex.save()
            n += 1
        if n:
            per_tenant[tenant.name] = n
            swept_total += n

    log.info("codexec: swept %d stuck run(s) across tenants", swept_total)
    return {"swept": swept_total, "by_tenant": per_tenant}
