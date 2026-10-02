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


class SpecFormat(models.TextChoices):
    """How the spec is written — which is decided by the template, if any.

    A from-scratch requirement is Markdown the user reads and approves. A
    template-based one is the template's own configuration format (journey.yaml
    for PSP), because there the spec IS the thing that configures the product.
    The panel needs to know which, or it renders YAML through a Markdown
    renderer and shows the user a wall of run-together text.
    """

    MARKDOWN = "markdown", "Markdown"
    YAML = "yaml", "YAML"


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
    spec_format = models.CharField(
        max_length=16, choices=SpecFormat.choices, default=SpecFormat.MARKDOWN
    )
    # True while the spec on screen is the analyst's work-in-progress rather
    # than a finished one. A template interview fills its YAML in as it goes,
    # so the pane is populated long before there is anything to approve.
    spec_is_draft = models.BooleanField(default=False)

    # The app template this requirement is being built on, if any. Empty means
    # a from-scratch build. Templates live in the public schema, so this is a
    # slug plus the pinned version's uuid rather than a foreign key: a newer
    # published version must never change what an app was agreed and built on.
    template_slug = models.CharField(max_length=64, blank=True, default="")
    template_version = models.CharField(max_length=32, blank=True, default="")
    template_version_uuid = models.UUIDField(null=True, blank=True)

    # Bumped on every change to a draft spec, by the agent or by hand. The
    # panel polls it to know when to re-read, and a manual save must quote the
    # revision it started from so it cannot silently overwrite the agent.
    draft_revision = models.PositiveIntegerField(default=0)
    # The last validation result for a template spec: [{level, path, message}].
    validation_issues = models.JSONField(default=list, blank=True)
    # JSON Pointers the last change (an analyst turn or a manual save) touched,
    # so the panel can show the user what just moved.
    changed_paths = models.JSONField(default=list, blank=True)

    # One-pass drafting (template requirements): the analyst drafts the whole
    # journey from the user's documents, flags every value it did not take
    # straight from them, and leaves only real gaps as open decisions.
    mode = models.CharField(max_length=16, blank=True, default="")  # draft | interview
    reference_id = models.CharField(max_length=64, blank=True, default="")
    # [{path, kind: inferred|reference|default|missing, note, source?}]
    spec_flags = models.JSONField(default=list, blank=True)
    # [{id, path, question, options, recommended, why}]
    open_decisions = models.JSONField(default=list, blank=True)
    # User journeys the analyst describes as swimlane processes, alongside the
    # lifecycles the panel derives from the spec itself:
    # {processes: [{id, title, group?, lanes, nodes, flows}]}
    workflows = models.JSONField(default=dict, blank=True)

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

    @property
    def template(self):
        """The template version behind this requirement, or None.

        Pinned requirements resolve their own version even after the template
        moves on; one adopted before pinning existed resolves the current one.
        """
        from .app_templates import get_template

        if not self.template_slug:
            return None
        return get_template(self.template_slug, version_uuid=self.template_version_uuid)

    def adopt_template(self, slug: str, version_uuid=None) -> bool:
        """Record that the user chose a template. Returns whether it changed.

        The version is pinned here — the current one unless ``version_uuid``
        names another — and the spec format follows from the template, so this
        is also the moment the requirement stops being a Markdown one.
        """
        from .app_templates import get_template

        template = get_template(slug, version_uuid=version_uuid)
        if template is None or (
            self.template_slug == template.slug
            and str(self.template_version_uuid or "") == template.version_uuid
        ):
            return False
        self.template_slug = template.slug
        self.template_version = template.version
        self.template_version_uuid = template.version_uuid or None
        self.spec_format = SpecFormat.YAML if template.is_yaml else SpecFormat.MARKDOWN
        return True

    def record_draft_spec(self, text: str) -> bool:
        """The spec as it stands mid-interview.

        Deliberately *not* versioned: a template interview re-emits the whole
        journey after every answer, and a version row per keystroke would bury
        the revisions that were actually agreed. The pane reads this field, so
        the user still watches the spec fill in.
        """
        text = (text or "").strip()
        if not text or text == self.spec_markdown.strip():
            return False
        self.spec_markdown = text
        self.spec_is_draft = True
        self.draft_revision += 1
        return True

    def record_spec(self, markdown: str, source: str = SpecSource.AGENT) -> None:
        """Store a new spec revision, keeping the previous one."""
        markdown = (markdown or "").strip()
        if not markdown:
            return
        # A finished spec that matches the draft already on screen is still a
        # revision worth recording: the draft was never versioned, so without
        # this the first approved spec would have no history row at all.
        if markdown == self.spec_markdown.strip() and not self.spec_is_draft:
            return
        self.spec_version += 1
        self.spec_markdown = markdown
        self.spec_is_draft = False
        AgentRequirementVersion.objects.create(
            requirement=self,
            version=self.spec_version,
            spec_markdown=markdown,
            spec_format=self.spec_format,
            template_version=self.template_version,
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


class AgentRequirementDocument(models.Model):
    """A document the user gave the analyst (SOP, RFP, protocol…), with its text."""

    requirement = models.ForeignKey(
        AgentRequirement, on_delete=models.CASCADE, related_name="documents"
    )
    name = models.CharField(max_length=160)
    content_type = models.CharField(max_length=120)
    size = models.PositiveIntegerField(default=0)
    sha256 = models.CharField(max_length=64)
    data = models.BinaryField()
    extracted_text = models.TextField(blank=True, default="")
    pages = models.PositiveIntegerField(default=0)
    sheets = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "agent_mode_requirement_document"
        ordering = ["requirement", "pk"]

    def __str__(self) -> str:
        return self.name


class AgentRequirementVersion(models.Model):
    """Spec history, so edits and regenerations can be compared."""

    requirement = models.ForeignKey(
        AgentRequirement, on_delete=models.CASCADE, related_name="versions"
    )
    version = models.PositiveIntegerField()
    spec_markdown = models.TextField()
    spec_format = models.CharField(
        max_length=16, choices=SpecFormat.choices, default=SpecFormat.MARKDOWN
    )
    source = models.CharField(
        max_length=8, choices=SpecSource.choices, default=SpecSource.AGENT
    )
    # The template version the spec was written against, when there is one.
    template_version = models.CharField(max_length=32, blank=True, default="")
    # A checkpoint of a draft (one per analyst turn), not an agreed revision.
    is_draft = models.BooleanField(default=False)
    # JSON Pointers the turn or edit changed, for the panel's highlights.
    changed_paths = models.JSONField(default=list, blank=True)
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
    # A build of a template requirement: the version it was built against,
    # and the approved journey written to disk for the build agent to read.
    template_version_uuid = models.UUIDField(null=True, blank=True)
    spec_path = models.CharField(max_length=1024, blank=True, default="")
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
