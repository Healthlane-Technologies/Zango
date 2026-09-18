"""Models for Agent Mode — AI-driven app development from the App Panel.

A run drives the Claude Agent SDK against a single app's workspace
(``<BASE_DIR>/workspaces/<tenant.name>/``) and records everything the agent
does as an append-only event stream, so the panel can tail it while the run
is still going.

Shape deliberately mirrors ``zango.apps.code_execution`` (CodeExecution /
CodeExecutionLogLine) — same status vocabulary, same monotonic ``seq``
contract for the tail endpoint, same terminal-state semantics.
"""

from __future__ import annotations

import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone

from zango.core.model_mixins import FullAuditMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RunStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    RUNNING = "running", "Running"
    # Agent stream finished; the migration/sync pipeline is still running.
    SYNCING = "syncing", "Syncing"
    SUCCESS = "success", "Success"
    # Agent succeeded but a post-run step failed — the most likely outcome
    # worth distinguishing in the UI.
    PARTIAL = "partial", "Completed with sync errors"
    FAILED = "failed", "Failed"
    TIMEOUT = "timeout", "Timed out"
    ABORTED = "aborted", "Aborted"


# Terminal states — set ended_at, release the single-active-run slot.
TERMINAL_STATUSES = frozenset(
    {
        RunStatus.SUCCESS,
        RunStatus.PARTIAL,
        RunStatus.FAILED,
        RunStatus.TIMEOUT,
        RunStatus.ABORTED,
    }
)

# States that hold the single-active-run slot for an app.
ACTIVE_STATUSES = frozenset({RunStatus.QUEUED, RunStatus.RUNNING, RunStatus.SYNCING})


class RequirementStatus(models.TextChoices):
    GATHERING = "gathering", "Gathering requirements"
    # The agent has produced a spec it believes is complete.
    READY = "ready", "Ready for review"
    APPROVED = "approved", "Approved"
    ABANDONED = "abandoned", "Abandoned"


REQUIREMENT_OPEN_STATUSES = frozenset(
    {RequirementStatus.GATHERING, RequirementStatus.READY}
)


class MessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"
    SYSTEM = "system", "System"


class SpecSource(models.TextChoices):
    AGENT = "agent", "Agent"
    USER = "user", "Edited by user"


class TriggerKind(models.TextChoices):
    UI = "ui", "App Settings UI"
    API = "api", "API"
    RESUME = "resume", "Resume / continue"
    RETRY = "retry", "Retry"


class EventKind(models.TextChoices):
    SYS = "sys", "Runner narration"
    INIT = "init", "Session init"
    ASSISTANT = "assistant", "Assistant text"
    THINKING = "thinking", "Thinking"
    TOOL_USE = "tool_use", "Tool use"
    TOOL_RESULT = "tool_result", "Tool result"
    SKILL = "skill", "Skill invocation"
    USER = "user", "User / tool feedback"
    COMPACT = "compact", "Context compaction"
    HOOK_DENY = "hook_deny", "Blocked by policy"
    POST_STEP = "post_step", "Post-run step"
    STDOUT = "stdout", "Subprocess stdout"
    STDERR = "stderr", "Subprocess stderr"
    RESULT = "result", "Result"
    ERROR = "error", "Error"


class RunPhase(models.TextChoices):
    """Coarse stages of a development run, for the progress timeline.

    The panel shows these instead of raw tool calls; the underlying events
    stay available behind a detail toggle.
    """

    PREPARING = "preparing", "Preparing"
    PLANNING = "planning", "Planning"
    BUILDING = "building", "Building"
    WIRING = "wiring", "Wiring up"
    APPLYING = "applying", "Applying changes"
    USERS = "users", "Roles & test users"
    DONE = "done", "Finished"


RUN_PHASE_ORDER = [
    RunPhase.PREPARING,
    RunPhase.PLANNING,
    RunPhase.BUILDING,
    RunPhase.WIRING,
    RunPhase.APPLYING,
    RunPhase.USERS,
    RunPhase.DONE,
]


class EventLevel(models.TextChoices):
    INFO = "info", "INFO"
    WARN = "warn", "WARN"
    ERR = "err", "ERROR"
    SYS = "sys", "system"


# ---------------------------------------------------------------------------
# Requirement (phase 1 — conversational gathering)
# ---------------------------------------------------------------------------


class AgentRequirement(FullAuditMixin):
    """A conversation that turns a rough ask into a buildable spec.

    Phase 1 of Agent Mode. The agent interviews the user — with read-only
    access to the workspace, so its questions can reference what already
    exists — and converges on an MVP-scoped specification. Only once that is
    approved does a development run become possible.

    Kept separate from AgentRun so a spec can outlive a failed build and be
    re-run without re-gathering.
    """

    object_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, editable=False
    )
    title = models.CharField(max_length=255, blank=True, default="")
    initial_prompt = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=RequirementStatus.choices,
        default=RequirementStatus.GATHERING,
        db_index=True,
    )

    # The current spec. History lives in AgentRequirementVersion.
    spec_markdown = models.TextField(blank=True, default="")
    spec_version = models.PositiveIntegerField(default=0)

    # SDK session, so each conversational turn resumes rather than restarts.
    session_id = models.CharField(max_length=128, blank=True, default="")

    turns = models.PositiveIntegerField(default=0)
    total_cost_usd = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )

    # Set while a turn is in flight, so the UI can disable input and a second
    # submit cannot race.
    is_thinking = models.BooleanField(default=False)
    celery_task_id = models.CharField(max_length=64, blank=True, default="")
    error_message = models.TextField(blank=True, default="")

    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=255, blank=True, default="")
    created_by_label = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "agent_mode_requirement"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    @property
    def is_open(self) -> bool:
        return self.status in REQUIREMENT_OPEN_STATUSES

    @property
    def can_build(self) -> bool:
        return self.status == RequirementStatus.APPROVED and bool(self.spec_markdown)

    def record_spec(self, markdown: str, source: str = SpecSource.AGENT) -> None:
        """Store a new spec revision, keeping the previous one."""
        markdown = (markdown or "").strip()
        if not markdown or markdown == self.spec_markdown.strip():
            return
        self.spec_version += 1
        self.spec_markdown = markdown
        AgentRequirementVersion.objects.create(
            requirement=self,
            version=self.spec_version,
            spec_markdown=markdown,
            source=source,
        )

    def __str__(self) -> str:
        return f"{self.title or self.initial_prompt[:40]} ({self.status})"


class AgentRequirementMessage(models.Model):
    """One conversational turn. Append-only; powers the chat pane."""

    requirement = models.ForeignKey(
        AgentRequirement, on_delete=models.CASCADE, related_name="messages"
    )
    seq = models.PositiveIntegerField()
    role = models.CharField(max_length=12, choices=MessageRole.choices)
    content = models.TextField(blank=True, default="")
    ts = models.DateTimeField(auto_now_add=True)
    # True when the assistant is asking rather than concluding — lets the UI
    # signal that a reply is expected.
    is_question = models.BooleanField(default=False)
    # Structured choices for this question, so the user answers by clicking
    # instead of writing prose. Empty for a reply that offered none; the chat
    # box is always still there, so this is an affordance, not a gate.
    questions = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "agent_mode_requirement_message"
        ordering = ["requirement", "seq"]
        constraints = [
            models.UniqueConstraint(
                fields=["requirement", "seq"], name="agent_mode_req_msg_unique_seq"
            )
        ]
        indexes = [models.Index(fields=["requirement", "seq"])]

    def __str__(self) -> str:
        return f"{self.requirement_id}:{self.seq}:{self.role}"


class AgentRequirementVersion(models.Model):
    """Spec history, so edits and regenerations can be compared."""

    requirement = models.ForeignKey(
        AgentRequirement, on_delete=models.CASCADE, related_name="versions"
    )
    version = models.PositiveIntegerField()
    spec_markdown = models.TextField()
    source = models.CharField(
        max_length=8, choices=SpecSource.choices, default=SpecSource.AGENT
    )
    ts = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "agent_mode_requirement_version"
        ordering = ["requirement", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["requirement", "version"],
                name="agent_mode_req_version_unique",
            )
        ]


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


class AgentRun(FullAuditMixin):
    """One Agent Mode run against this app's workspace."""

    object_uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, editable=False
    )

    # --- request ---------------------------------------------------------
    prompt = models.TextField()
    title = models.CharField(max_length=255, blank=True, default="")
    trigger_kind = models.CharField(
        max_length=16, choices=TriggerKind.choices, default=TriggerKind.UI
    )
    # The approved spec this run was built from, when there is one.
    requirement = models.ForeignKey(
        "AgentRequirement",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="runs",
    )
    triggered_by = models.CharField(max_length=255, blank=True, default="")

    # --- execution -------------------------------------------------------
    status = models.CharField(
        max_length=16,
        choices=RunStatus.choices,
        default=RunStatus.QUEUED,
        db_index=True,
    )
    celery_task_id = models.CharField(max_length=64, blank=True, default="")

    # True while in flight, NULL once terminal. A partial unique index on
    # this column is what actually guarantees one active run per app —
    # NULLs are not unique-constrained, so terminal rows don't collide.
    is_active = models.BooleanField(null=True, default=True)
    abort_requested = models.BooleanField(default=False)

    queued_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    agent_ended_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)

    # --- agent configuration actually used (audit; never re-derived) -----
    model = models.CharField(max_length=64, blank=True, default="")
    effort = models.CharField(max_length=16, blank=True, default="")
    permission_mode = models.CharField(max_length=32, blank=True, default="")
    max_turns = models.PositiveIntegerField(null=True, blank=True)
    max_budget_usd = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True
    )
    skill_name = models.CharField(max_length=128, blank=True, default="")
    workspace_path = models.CharField(max_length=1024, blank=True, default="")

    # --- session (resume / fork) -----------------------------------------
    session_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    resumed_from = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resumes",
    )

    # --- result (from ResultMessage) -------------------------------------
    result_subtype = models.CharField(max_length=32, blank=True, default="")
    terminal_reason = models.CharField(max_length=64, blank=True, default="")
    result_text = models.TextField(blank=True, default="")
    num_turns = models.PositiveIntegerField(null=True, blank=True)
    duration_api_ms = models.PositiveIntegerField(null=True, blank=True)
    total_cost_usd = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )
    # Summed from ResultMessage.model_usage (camelCase keys, passed through
    # from the CLI verbatim) — there is no total_input_tokens on the SDK type.
    input_tokens = models.PositiveBigIntegerField(null=True, blank=True)
    output_tokens = models.PositiveBigIntegerField(null=True, blank=True)
    cache_read_tokens = models.PositiveBigIntegerField(null=True, blank=True)
    cache_creation_tokens = models.PositiveBigIntegerField(null=True, blank=True)
    model_usage = models.JSONField(null=True, blank=True)

    # --- failure ---------------------------------------------------------
    error_type = models.CharField(max_length=128, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    error_traceback = models.TextField(blank=True, default="")
    api_error_status = models.PositiveIntegerField(null=True, blank=True)

    # --- change tracking / rollback --------------------------------------
    snapshot_path = models.CharField(max_length=1024, blank=True, default="")
    snapshot_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    files_changed = models.JSONField(null=True, blank=True)
    tool_use_counts = models.JSONField(null=True, blank=True)
    post_steps = models.JSONField(null=True, blank=True)
    # Test users created for this run, with one-time temporary passwords.
    test_users = models.JSONField(null=True, blank=True)
    requires_restart = models.BooleanField(default=False)

    class Meta:
        db_table = "agent_mode_run"
        ordering = ["-queued_at"]
        indexes = [
            models.Index(fields=["status", "-queued_at"]),
            models.Index(fields=["-queued_at"]),
        ]
        constraints = [
            # At most one in-flight run per app (per tenant schema), enforced
            # by Postgres rather than by a racy SELECT in the view.
            models.UniqueConstraint(
                fields=["is_active"],
                condition=Q(is_active=True),
                name="agent_mode_single_active_run",
            ),
        ]

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    def finalize(self, status: str, **fields) -> None:
        """Move the run to a terminal state.

        Centralised so releasing the single-active-run slot (is_active=None)
        can never be forgotten — a stuck True would block every later run.
        """
        if status not in TERMINAL_STATUSES:
            raise ValueError(f"{status!r} is not a terminal status")

        self.status = status
        self.is_active = None
        self.ended_at = fields.pop("ended_at", None) or timezone.now()
        if self.started_at and self.duration_ms is None:
            delta = (self.ended_at - self.started_at).total_seconds()
            self.duration_ms = int(delta * 1000)

        update_fields = {
            "status",
            "is_active",
            "ended_at",
            "duration_ms",
            "modified_at",
        }
        for key, value in fields.items():
            setattr(self, key, value)
            update_fields.add(key)
        self.save(update_fields=sorted(update_fields))

    def __str__(self) -> str:
        return f"{self.object_uuid} ({self.status})"


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class AgentRunEvent(models.Model):
    """Append-only event from a run. Powers the live transcript tail.

    Written in autocommitted batches so the tail endpoint sees rows while the
    run is still in progress. Pruned on a schedule.
    """

    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="events")
    # Monotonic within a run — what /event-tail/?after_seq=N keys on.
    seq = models.PositiveIntegerField()
    ts = models.DateTimeField(auto_now_add=True)
    kind = models.CharField(max_length=16, choices=EventKind.choices, db_index=True)
    phase = models.CharField(
        max_length=12,
        choices=RunPhase.choices,
        default=RunPhase.PREPARING,
        db_index=True,
    )
    level = models.CharField(
        max_length=8, choices=EventLevel.choices, default=EventLevel.INFO
    )
    # Human-renderable one-liner, capped and secret-redacted before insert.
    message = models.TextField(blank=True, default="")
    tool_name = models.CharField(max_length=64, blank=True, default="")
    tool_use_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    # Attributes output to a subagent (Task); NULL for the main agent.
    parent_tool_use_id = models.CharField(max_length=64, blank=True, default="")
    is_error = models.BooleanField(default=False)
    data = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "agent_mode_run_event"
        ordering = ["run", "seq"]
        constraints = [
            models.UniqueConstraint(
                fields=["run", "seq"], name="agent_mode_event_unique_seq"
            ),
        ]
        indexes = [
            models.Index(fields=["run", "seq"]),
            models.Index(fields=["run", "kind", "seq"]),
        ]

    def __str__(self) -> str:
        return f"{self.run_id}:{self.seq}:{self.kind}"
