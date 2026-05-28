"""Models for the Code Execution feature.

Two-level file design:
- CodeSnippetFile lives on a saved snippet, persisted on Save.
- CodeExecFile lives on a specific execution, snapshotted from snippet files
  on run trigger, and additionally populated with outputs at run time.

Storage blobs are shared between snippet and exec files via the `file.name`
(storage path). The blob is reference-counted at GC time — see
docs/code-execution-spec.html.
"""

from __future__ import annotations

import hashlib
import uuid

from django.db import models
from django.utils.text import slugify

from zango.apps.auditlogs.registry import auditlog
from zango.core.model_mixins import FullAuditMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExecStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    TIMEOUT = "timeout", "Timed out"
    ABORTED = "aborted", "Aborted"


class TriggerKind(models.TextChoices):
    UI_RUN = "ui_run", "Run from UI"
    UI_SAVE_RUN = "ui_save_run", "Save & Run from UI"
    API = "api", "API"
    RETRY = "retry", "Retry"


class FileKind(models.TextChoices):
    INPUT = "input", "Input"
    OUTPUT = "output", "Output"


# Terminal states — set ended_at, lock the run row.
TERMINAL_STATUSES = frozenset(
    {ExecStatus.SUCCESS, ExecStatus.FAILED, ExecStatus.TIMEOUT, ExecStatus.ABORTED}
)


# ---------------------------------------------------------------------------
# Snippet
# ---------------------------------------------------------------------------


def _snippet_file_upload_to(instance: "CodeSnippetFile", filename: str) -> str:
    return f"codexec/snippets/{instance.snippet_id}/{uuid.uuid4().hex}"


def _exec_file_upload_to(instance: "CodeExecFile", filename: str) -> str:
    return f"codexec/runs/{instance.execution_id}/{instance.kind}/{uuid.uuid4().hex}"


class CodeSnippet(FullAuditMixin):
    """A named, versioned executable Python buffer in a tenant's codebase."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    code = models.TextField(default="")
    code_hash = models.CharField(max_length=64, blank=True, default="")
    version = models.PositiveIntegerField(default=1)
    timeout_seconds = models.PositiveIntegerField(default=60)
    is_archived = models.BooleanField(default=False)

    class Meta:
        db_table = "code_execution_snippet"
        ordering = ["-modified_at"]
        indexes = [
            models.Index(fields=["is_archived", "-modified_at"]),
        ]

    def save(self, *args, **kwargs):
        # Hash the current code for cheap dedup / tamper detection.
        if self.code:
            self.code_hash = hashlib.sha256(self.code.encode("utf-8")).hexdigest()
        else:
            self.code_hash = ""
        if not self.slug:
            base = slugify(self.name)[:56] or "snippet"
            self.slug = f"{base}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def bump_version(self) -> None:
        self.version = (self.version or 0) + 1

    def __str__(self) -> str:
        return self.name


class CodeSnippetFile(FullAuditMixin):
    """An input file attached to a snippet — persists across runs.

    On a run, each row is snapshotted into a CodeExecFile(kind=input)
    sharing the underlying storage blob. Hard-deleted from the model when
    the user removes it; past CodeExecFile rows are unaffected because the
    `source_snippet_file` FK is `SET_NULL`.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snippet = models.ForeignKey(
        CodeSnippet, on_delete=models.CASCADE, related_name="files"
    )
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=_snippet_file_upload_to, max_length=512)
    size_bytes = models.PositiveBigIntegerField(default=0)
    content_type = models.CharField(max_length=128, blank=True, default="")
    sha256 = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "code_execution_snippet_file"
        constraints = [
            models.UniqueConstraint(
                fields=["snippet", "name"], name="codexec_snippetfile_unique_name"
            ),
        ]
        ordering = ["name"]
        indexes = [models.Index(fields=["snippet", "name"])]

    def __str__(self) -> str:
        return f"{self.snippet_id}:{self.name}"


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


class CodeExecution(FullAuditMixin):
    """One row per run. Self-contained history record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snippet = models.ForeignKey(
        CodeSnippet, on_delete=models.PROTECT, related_name="executions"
    )
    snippet_version = models.PositiveIntegerField()
    source_snapshot = models.TextField()
    source_hash = models.CharField(max_length=64, db_index=True)

    status = models.CharField(
        max_length=16,
        choices=ExecStatus.choices,
        default=ExecStatus.QUEUED,
        db_index=True,
    )
    celery_task_id = models.CharField(max_length=64, blank=True, default="")

    queued_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    # Captured streams — cumulative for the run, capped at 1 MB / 256 KB.
    stdout = models.TextField(blank=True, default="")
    stderr = models.TextField(blank=True, default="")

    return_value = models.JSONField(null=True, blank=True)
    return_value_truncated = models.BooleanField(default=False)

    exception_type = models.CharField(max_length=128, blank=True, default="")
    exception_message = models.TextField(blank=True, default="")
    exception_traceback = models.TextField(blank=True, default="")

    triggered_by = models.CharField(max_length=255, blank=True, default="")
    trigger_kind = models.CharField(
        max_length=16, choices=TriggerKind.choices, default=TriggerKind.UI_RUN
    )

    class Meta:
        db_table = "code_execution_run"
        ordering = ["-queued_at"]
        indexes = [
            models.Index(fields=["snippet", "-queued_at"]),
            models.Index(fields=["status", "-queued_at"]),
        ]

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    def __str__(self) -> str:
        return f"{self.snippet_id}/{self.id}"


class CodeExecFile(FullAuditMixin):
    """Input or output file tied to a single execution.

    For inputs, snapshotted from a CodeSnippetFile at run trigger — same
    storage blob. For outputs, written during the run via the codexec helper.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(
        CodeExecution, on_delete=models.CASCADE, related_name="files"
    )
    kind = models.CharField(max_length=8, choices=FileKind.choices, db_index=True)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to=_exec_file_upload_to, max_length=512)
    source_snippet_file = models.ForeignKey(
        CodeSnippetFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="snapshots",
    )
    size_bytes = models.PositiveBigIntegerField(default=0)
    content_type = models.CharField(max_length=128, blank=True, default="")
    sha256 = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "code_execution_run_file"
        constraints = [
            models.UniqueConstraint(
                fields=["execution", "kind", "name"],
                name="codexec_execfile_unique_name",
            ),
        ]
        ordering = ["kind", "name"]
        indexes = [
            models.Index(fields=["execution", "kind"]),
            models.Index(fields=["execution", "kind", "name"]),
        ]

    def __str__(self) -> str:
        return f"{self.execution_id}:{self.kind}:{self.name}"


# ---------------------------------------------------------------------------
# Audit registration
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Log lines (Phase 2 — per-line capture for the live tail)
# ---------------------------------------------------------------------------


class LogLevel(models.TextChoices):
    OUT = "out", "stdout"
    ERR = "err", "stderr"
    INFO = "info", "INFO"
    WARN = "warn", "WARN"
    SYS = "sys", "system"


class CodeExecutionLogLine(models.Model):
    """Append-only log line. Powers the live tail. Pruned at 90 days."""

    execution = models.ForeignKey(
        CodeExecution, on_delete=models.CASCADE, related_name="log_lines"
    )
    # Monotonic sequence within a run — what the /log-tail/?after_seq=N filter keys on.
    seq = models.PositiveIntegerField()
    ts = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=8, choices=LogLevel.choices)
    message = models.TextField()

    class Meta:
        db_table = "code_execution_log_line"
        ordering = ["execution", "seq"]
        constraints = [
            models.UniqueConstraint(
                fields=["execution", "seq"], name="codexec_logline_unique_seq"
            ),
        ]
        indexes = [
            models.Index(fields=["execution", "seq"]),
        ]


# ---------------------------------------------------------------------------
# Audit registration
# ---------------------------------------------------------------------------

auditlog.register(CodeSnippet)
auditlog.register(CodeSnippetFile)
auditlog.register(CodeExecution)
auditlog.register(CodeExecFile)
