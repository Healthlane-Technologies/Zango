"""Celery entry point for an Agent Mode run.

Ordering in ``agent_run_executor`` is load-bearing:

1. Resolve credentials **first**, while the connection is still on the public
   schema — ``AgentModeSettings`` lives there, and reading it after
   ``set_tenant`` would hit the tenant's search_path.
2. Bind the tenant, then re-check the suspend guard locally (this task does
   not route through ``zango_task_executor``).

``Workspace.ready()`` is deliberately never called: the runner must not
import workspace code, both to keep pluginbase state out of this process and
so a run is still possible against an app whose code is currently broken.

Every ORM write happens on this thread. The SDK iteration runs on a separate
pump thread that touches only a queue — see ``stream.py`` for why.
"""

from __future__ import annotations

import logging
import os
import re
import time
import traceback

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from django.db import connection
from django.utils import timezone


logger = logging.getLogger("zango.agent_mode")

ABORT_POLL_SECONDS = 1.0


# Phase inference from the agent's own actions. Only ever moves forward, so a
# stray late Read cannot drag the timeline back to Planning.
_WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}


def _phase_for_message(message, current: str) -> str:
    """Advance the run phase based on what the agent just did."""
    from .models import RUN_PHASE_ORDER, RunPhase

    if type(message).__name__ != "AssistantMessage":
        return current

    suggested = current
    for block in getattr(message, "content", None) or []:
        if type(block).__name__ != "ToolUseBlock":
            continue
        name = getattr(block, "name", "") or ""
        tool_input = getattr(block, "input", None) or {}
        if name in _WRITE_TOOLS:
            suggested = RunPhase.BUILDING
        elif name == "Bash":
            command = str(tool_input.get("command", ""))
            if "manage.py" in command:
                suggested = RunPhase.APPLYING
            elif "configure" in command or "appbuilder" in command:
                suggested = RunPhase.WIRING

    try:
        if RUN_PHASE_ORDER.index(suggested) > RUN_PHASE_ORDER.index(current):
            return suggested
    except ValueError:
        pass
    return current


_ROLE_LINE = re.compile(r"^\s*[-*]\s*\*\*(?P<name>[^*]{2,50})\*\*", re.M)


def _roles_from_text(spec: str) -> list:
    """Role names from the spec's "Roles and access" section.

    Best-effort and deliberately narrow: it only reads bold list items under a
    roles heading, so ordinary prose cannot conjure a role.
    """
    if not spec:
        return []
    lines = spec.splitlines()
    names, in_section = [], False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            in_section = bool(re.search(r"roles?\b", stripped, re.I))
            continue
        if not in_section:
            continue
        match = _ROLE_LINE.match(line)
        if match:
            name = match.group("name").strip().strip(":").strip()
            if name and name not in names:
                names.append(name)
    return names


def _precreate_roles(names: list) -> list:
    """Create spec roles up front. Never raises — a failure here must not stop
    the build, it just means the agent cannot configure that role's menu."""
    from .roles import RESERVED_ROLES, _attach_user_access

    created = []
    try:
        from zango.apps.appauth.models import UserRoleModel

        for name in names:
            if name in RESERVED_ROLES or len(name) > 50:
                continue
            if UserRoleModel.objects.filter(name=name).exists():
                continue
            role = UserRoleModel.objects.create(name=name, is_active=True)
            _attach_user_access(role)
            created.append(name)
    except Exception:  # noqa: BLE001
        logger.exception("agent_mode: could not pre-create roles")
    return created


def _abort_requested(run_id: int) -> bool:
    from .models import AgentRun

    try:
        return (
            AgentRun.objects.filter(pk=run_id)
            .values_list("abort_requested", flat=True)
            .first()
            or False
        )
    except Exception:  # noqa: BLE001
        return False


def _apply_state(run, state: dict) -> None:
    """Copy accumulated stream state onto the run row **and save it**.

    Saving here is load-bearing: ``finalize()`` writes with an explicit
    ``update_fields``, so anything set on the instance but not listed there is
    silently discarded. The first real run lost its cost, turns, tokens,
    session id and tool counts exactly that way.
    """
    from .recorder import MESSAGE_CAP

    run.session_id = (state.get("session_id") or run.session_id or "")[:128]
    run.result_subtype = (state.get("result_subtype") or "")[:32]
    run.terminal_reason = (state.get("terminal_reason") or "")[:64]
    run.result_text = (state.get("result_text") or "")[: MESSAGE_CAP * 32]
    run.num_turns = state.get("num_turns")
    run.duration_api_ms = state.get("duration_api_ms")
    run.api_error_status = state.get("api_error_status")
    if state.get("total_cost_usd") is not None:
        run.total_cost_usd = state["total_cost_usd"]
    for field in (
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_creation_tokens",
    ):
        if state.get(field) is not None:
            setattr(run, field, state[field])
    run.tool_use_counts = state.get("tool_use_counts") or {}
    # Which models actually ran, and what each cost. Falls back to the models
    # seen on assistant messages when the run died before a ResultMessage.
    usage = state.get("model_usage")
    if not usage and state.get("models_seen"):
        usage = {
            name: {"messages": count}
            for name, count in state["models_seen"].items()
        }
    if usage:
        run.model_usage = usage

    run.save(
        update_fields=[
            "session_id",
            "result_subtype",
            "terminal_reason",
            "result_text",
            "num_turns",
            "duration_api_ms",
            "api_error_status",
            "total_cost_usd",
            "input_tokens",
            "output_tokens",
            "cache_read_tokens",
            "cache_creation_tokens",
            "tool_use_counts",
            "model_usage",
            "modified_at",
        ]
    )


@shared_task(bind=True, name="zango.agent_mode.agent_run_executor")
def agent_run_executor(self, run_uuid: str, tenant_name: str) -> dict:
    from zango.apps.shared.tenancy.models import TenantModel

    from .context import build_app_context, workspaces_root
    from .credentials import resolve_credentials
    from .models import AgentRun, RunStatus

    # 1. Public-schema read must happen before set_tenant.
    creds = resolve_credentials()

    tenant = TenantModel.objects.get(name=tenant_name)
    connection.set_tenant(tenant)

    try:
        run = AgentRun.objects.get(object_uuid=run_uuid)
    except AgentRun.DoesNotExist:
        logger.error("agent_mode: run %s not found in %s", run_uuid, tenant_name)
        return {"status": "missing"}

    if run.is_terminal:
        return {"status": run.status}

    if getattr(tenant, "status", "") == "suspended":
        run.finalize(
            RunStatus.ABORTED,
            error_type="TenantSuspended",
            error_message="The app is suspended; Agent Mode refused to run.",
        )
        return {"status": run.status}

    if not creds.is_usable:
        run.finalize(
            RunStatus.FAILED,
            error_type="MissingCredentials",
            error_message=(
                "No Anthropic credential configured. Set ANTHROPIC_API_KEY or "
                "configure Agent Mode settings."
            ),
        )
        return {"status": run.status}

    run.status = RunStatus.RUNNING
    run.started_at = timezone.now()
    run.celery_task_id = (self.request.id or "")[:64]
    run.save(update_fields=["status", "started_at", "celery_task_id", "modified_at"])

    return _execute(run, tenant, creds, workspaces_root(), build_app_context)


def _execute(run, tenant, creds, ws_root, build_app_context) -> dict:
    from .mapper import record_message
    from .models import RUN_PHASE_ORDER, EventKind, EventLevel, RunPhase, RunStatus  # noqa: F401
    from .options import build_agent_options
    from .prompt import QUALIFIED_SKILL, compose_prompt, compose_resume_prompt
    from .postrun import requires_restart, run_post_steps, run_step
    from .recorder import EventRecorder
    from .roles import ensure_roles
    from .users import ensure_users
    from .settings_writer import write_run_settings
    from .snapshot import create_snapshot, diff_manifest, workspace_manifest
    from .stream import AgentStream

    from django.conf import settings as dj

    recorder = EventRecorder(run)
    state: dict = {}
    baseline_manifest = None
    stream = None
    status = RunStatus.FAILED
    extra: dict = {}

    try:
        ctx = build_app_context(tenant)
        if not ctx.workspace_exists:
            raise RuntimeError(f"workspace not found: {ctx.workspace_path}")

        run_dir = os.path.join(
            str(dj.BASE_DIR), ".agent_mode", "runs", tenant.name, str(run.object_uuid)
        )
        settings_path = write_run_settings(
            run_dir=run_dir,
            workspace_path=ctx.workspace_path,
            workspaces_root=ws_root,
            base_dir=str(dj.BASE_DIR),
            project_name=os.path.basename(str(dj.BASE_DIR)),
        )
        run.workspace_path = ctx.workspace_path[:1024]
        run.skill_name = QUALIFIED_SKILL[:128]
        run.save(update_fields=["workspace_path", "skill_name", "modified_at"])

        recorder.emit(
            EventKind.SYS,
            f"Starting Agent Mode in {ctx.workspace_path}",
            level=EventLevel.SYS,
            data={"packages": ctx.packages, "modules": ctx.modules},
        )

        # The only undo. Taken before the agent can write anything; over the
        # size ceiling it is skipped loudly rather than blocking the run.
        snapshot = create_snapshot(
            ctx.workspace_path,
            run_dir,
            int(getattr(dj, "AGENT_MODE_SNAPSHOT_MAX_BYTES", 536870912)),
        )
        if snapshot.ok:
            run.snapshot_path = snapshot.path[:1024]
            run.snapshot_bytes = snapshot.size_bytes
            run.save(update_fields=["snapshot_path", "snapshot_bytes", "modified_at"])
            recorder.emit(
                EventKind.SYS,
                f"Workspace snapshot taken ({snapshot.size_bytes / 1e6:.1f} MB, "
                f"{len(snapshot.manifest)} files)",
                level=EventLevel.SYS,
            )
        else:
            recorder.emit(
                EventKind.SYS,
                f"No snapshot taken — {snapshot.skipped_reason}. "
                "This run has no rollback point.",
                level=EventLevel.WARN,
            )

        # Packages before the agent starts. Without appbuilder/crud/workflow
        # there is no BaseCrudView, FormRenderer, workflow engine or route
        # config, and the agent falls back to hand-rolled Django views — which
        # is what the first real run produced.
        from .config import load_config

        agent_cfg = load_config()
        if agent_cfg.ensure_packages:
            recorder.emit(
                EventKind.SYS,
                "Ensuring Zango packages are installed…",
                level=EventLevel.SYS,
            )
            pkg = run_step(
                "ensure_packages",
                ["agent_mode_ensure_packages", tenant.name],
                str(dj.BASE_DIR),
                timeout=900,
            )
            for line in (pkg.stdout_tail or "").splitlines()[-30:]:
                if line.strip():
                    recorder.emit(EventKind.STDOUT, line)
            if pkg.returncode != 0:
                for line in (pkg.stderr_tail or "").splitlines()[-30:]:
                    if line.strip():
                        recorder.emit(
                            EventKind.STDERR, line, level=EventLevel.ERR, is_error=True
                        )
                raise RuntimeError(
                    "Could not install the required Zango packages "
                    "(appbuilder, crud, workflow). The agent would have had to "
                    "hand-roll Django views, so the run was stopped instead."
                )
            recorder.flush()
            # settings.json / manifest.json changed underneath us.
            ctx = build_app_context(tenant)
            # Re-baseline: the snapshot predates package installation, so
            # diffing against it would attribute every installed package file
            # to the agent. The first successful run reported 500 files added,
            # 480 of them packages/.
            baseline_manifest = workspace_manifest(ctx.workspace_path)

        if baseline_manifest is None:
            baseline_manifest = snapshot.manifest

        # Create any roles the spec names *before* the agent runs. AppBuilder's
        # create_config resolves a role by primary key, so a role that does not
        # exist yet has no ID for the agent to pass — the first successful run
        # registered routes but no menus for exactly this reason.
        spec_roles = _roles_from_text(run.prompt)
        if spec_roles:
            created = _precreate_roles(spec_roles)
            if created:
                recorder.emit(
                    EventKind.SYS,
                    f"Pre-created {len(created)} role(s) so menus can be "
                    f"configured: {', '.join(created)}",
                    level=EventLevel.SYS,
                    data={"roles": created},
                )

        recorder.set_phase(RunPhase.PLANNING)
        if run.resumed_from_id and run.resumed_from:
            previous = run.resumed_from
            reason = (
                f"{previous.error_type or previous.status}: "
                f"{(previous.error_message or '').strip()[:300]}"
            ).strip(": ")
            prompt = compose_resume_prompt(run.prompt, ctx, reason)
            recorder.emit(
                EventKind.SYS,
                f"Resuming run {str(previous.object_uuid)[:8]} "
                f"({previous.status}). Continuing, not restarting.",
                level=EventLevel.SYS,
            )
        else:
            prompt = compose_prompt(run.prompt, ctx)
        stream = AgentStream(options=None, prompt=prompt)
        stream.options = build_agent_options(
            run=run,
            ctx=ctx,
            creds=creds,
            settings_path=settings_path,
            hook_sink=stream.hook_sink,
            stderr_sink=recorder.emit_stderr,
        )

        last_abort_check = 0.0
        for item in stream:
            if item.kind == "idle":
                recorder.flush_if_stale()
            elif item.kind == "hook":
                payload = item.payload or {}
                recorder.emit(
                    EventKind.HOOK_DENY,
                    payload.get("reason", "blocked by policy"),
                    level=EventLevel.ERR,
                    tool_name=payload.get("tool_name", ""),
                    is_error=True,
                    data={"tool_input": payload.get("tool_input")},
                )
            elif item.kind == "message":
                recorder.set_phase(_phase_for_message(item.payload, recorder.phase))
                record_message(item.payload, recorder, state)
                recorder.flush_if_stale()
            elif item.kind == "done":
                break
            elif item.kind == "error":
                exc = item.payload
                extra = {
                    "error_type": type(exc).__name__[:128],
                    "error_message": str(exc)[:8000],
                    "error_traceback": "".join(
                        traceback.format_exception(type(exc), exc, exc.__traceback__)
                    )[:20000],
                }
                recorder.emit(
                    EventKind.ERROR,
                    f"{type(exc).__name__}: {exc}",
                    level=EventLevel.ERR,
                    is_error=True,
                )
                break

            now = time.monotonic()
            if now - last_abort_check >= ABORT_POLL_SECONDS:
                last_abort_check = now
                if _abort_requested(run.pk):
                    recorder.emit(
                        EventKind.SYS,
                        "Abort requested — interrupting the agent.",
                        level=EventLevel.WARN,
                    )
                    stream.request_stop()

        run.agent_ended_at = timezone.now()
        run.save(update_fields=["agent_ended_at", "modified_at"])

        # Always record the diff, even on failure: a run that stopped partway
        # still left files on disk, and the operator needs to see which.
        try:
            observed = diff_manifest(
                baseline_manifest, workspace_manifest(ctx.workspace_path)
            )
            run.files_changed = observed.to_dict()
            run.requires_restart = requires_restart(observed)
            run.save(update_fields=["files_changed", "requires_restart", "modified_at"])
        except Exception:  # noqa: BLE001
            logger.exception("agent_mode: could not record the file diff")

        if extra:
            status = RunStatus.FAILED
        elif _abort_requested(run.pk):
            # Post-run steps are deliberately skipped: a half-written module
            # must never be migrated.
            status = RunStatus.ABORTED
            recorder.emit(
                EventKind.SYS,
                "Run aborted — skipping migrations and sync.",
                level=EventLevel.WARN,
            )
        elif state.get("is_error"):
            status = RunStatus.FAILED
            subtype = state.get("result_subtype") or ""
            # The SDK reports a tripped ceiling as a normal result with
            # is_error set. Name it, so the panel does not present a budget
            # stop as an unexplained crash.
            known = {
                "error_max_budget_usd": (
                    "BudgetExhausted",
                    "The run hit its cost ceiling "
                    f"(${run.max_budget_usd}). Raise AGENT_MODE_MAX_BUDGET_USD "
                    "or narrow the requirement. Files already written were left "
                    "in place and no migrations were run.",
                ),
                "error_max_turns": (
                    "MaxTurnsReached",
                    "The run hit its turn limit. Raise AGENT_MODE_MAX_TURNS or "
                    "narrow the requirement.",
                ),
            }
            error_type, message = known.get(
                subtype, ("AgentError", state.get("result_text", "")[:8000])
            )
            extra = {"error_type": error_type, "error_message": message[:8000]}
        else:
            changes = diff_manifest(
                baseline_manifest, workspace_manifest(ctx.workspace_path)
            )
            run.files_changed = changes.to_dict()
            run.requires_restart = requires_restart(changes)
            run.status = RunStatus.SYNCING
            run.save(
                update_fields=[
                    "files_changed",
                    "requires_restart",
                    "status",
                    "modified_at",
                ]
            )
            recorder.emit(
                EventKind.SYS,
                f"Agent finished. {len(changes.added)} added, "
                f"{len(changes.modified)} modified, {len(changes.deleted)} deleted.",
                level=EventLevel.SYS,
                data=changes.to_dict(),
            )

            recorder.set_phase(RunPhase.USERS)
            # Roles first: sync_policies_with_roles silently drops policy
            # roles that do not exist, leaving views nobody can reach.
            role_results = ensure_roles(
                ctx.workspace_path,
                emit=lambda m, is_error=False: recorder.emit(
                    EventKind.SYS,
                    m,
                    level=EventLevel.ERR if is_error else EventLevel.SYS,
                    is_error=is_error,
                ),
            )
            created = [r.name for r in role_results if r.status == "created"]
            if created:
                recorder.emit(
                    EventKind.SYS,
                    f"Created {len(created)} app role(s): {', '.join(created)}",
                    level=EventLevel.SYS,
                    data={"roles": created},
                )

            # Test users last: they need their roles to exist first.
            user_results = ensure_users(
                ctx.workspace_path,
                emit=lambda m, is_error=False: recorder.emit(
                    EventKind.SYS,
                    m,
                    level=EventLevel.ERR if is_error else EventLevel.SYS,
                    is_error=is_error,
                ),
            )
            if user_results:
                run.test_users = [u.to_dict() for u in user_results]
                run.save(update_fields=["test_users", "modified_at"])
                made = [u.email for u in user_results if u.status == "created"]
                if made:
                    recorder.emit(
                        EventKind.SYS,
                        f"Created {len(made)} test user(s): {', '.join(made)}. "
                        "Passwords are on the run detail.",
                        level=EventLevel.SYS,
                    )

            def _emit(kind, message, data=None, is_error=False):
                recorder.emit(
                    kind,
                    message,
                    level=EventLevel.ERR if is_error else EventLevel.INFO,
                    is_error=is_error,
                    data=data,
                )
                recorder.flush_if_stale(0.5)

            recorder.set_phase(RunPhase.APPLYING)
            results = run_post_steps(
                app_name=tenant.name,
                base_dir=str(dj.BASE_DIR),
                changes=changes,
                emit=_emit,
            )
            run.post_steps = [r.to_dict() for r in results]
            run.save(update_fields=["post_steps", "modified_at"])

            failed = [r for r in results if not r.ok]
            if failed:
                status = RunStatus.PARTIAL
                extra = {
                    "error_type": "PostRunStepFailed",
                    "error_message": (
                        "The agent finished but "
                        + ", ".join(r.step for r in failed)
                        + " failed. The files are already written; restore the "
                        "pre-run snapshot with `manage.py agent_mode_restore` "
                        "if you need to roll back."
                    )[:8000],
                }
            else:
                status = RunStatus.SUCCESS

    except SoftTimeLimitExceeded:
        status = RunStatus.TIMEOUT
        extra = {
            "error_type": "SoftTimeLimitExceeded",
            "error_message": "The run exceeded its time limit.",
        }
        recorder.emit(
            EventKind.ERROR, "Run timed out.", level=EventLevel.ERR, is_error=True
        )
        if stream is not None:
            stream.request_stop()
    except Exception as exc:  # noqa: BLE001
        status = RunStatus.FAILED
        extra = {
            "error_type": type(exc).__name__[:128],
            "error_message": str(exc)[:8000],
            "error_traceback": traceback.format_exc()[:20000],
        }
        logger.exception("agent_mode: run %s failed", run.object_uuid)
        recorder.emit(
            EventKind.ERROR,
            f"{type(exc).__name__}: {exc}",
            level=EventLevel.ERR,
            is_error=True,
        )
    finally:
        recorder.set_phase(RunPhase.DONE)
        if stream is not None:
            stream.request_stop()
            stream.join(timeout=15)
        try:
            _apply_state(run, state)
        except Exception:  # noqa: BLE001
            logger.exception("agent_mode: failed to apply run state")
        recorder.flush()

    run.finalize(status, **extra)
    return {"status": run.status, "events": recorder.seq}


@shared_task(name="zango.agent_mode.sweep_stuck_agent_runs")
def sweep_stuck_agent_runs() -> dict:
    """Reap runs whose worker died, and runs stranded with no worker at all."""
    from datetime import timedelta

    from django.conf import settings as dj
    from django.db import connection as conn

    from zango.apps.shared.tenancy.models import TenantModel

    from .models import ACTIVE_STATUSES, AgentRun, RunStatus

    max_seconds = getattr(dj, "AGENT_MODE_MAX_RUN_SECONDS", 1800)
    now = timezone.now()
    running_cutoff = now - timedelta(seconds=int(max_seconds * 1.5))
    queued_cutoff = now - timedelta(minutes=15)
    reaped = 0

    for tenant in TenantModel.objects.exclude(schema_name="public"):
        try:
            conn.set_tenant(tenant)
            # A gathering turn whose worker died leaves the conversation
            # permanently "thinking", with the input box disabled and no way
            # back. Release those first.
            from .models import AgentRequirement

            stuck_turns = AgentRequirement.objects.filter(
                is_thinking=True, modified_at__lt=queued_cutoff
            )
            for requirement in stuck_turns:
                requirement.is_thinking = False
                requirement.error_message = (
                    "The agent did not reply — the worker may have restarted. "
                    "Send your message again."
                )
                requirement.save(
                    update_fields=["is_thinking", "error_message", "modified_at"]
                )
                reaped += 1

            stale = AgentRun.objects.filter(status__in=list(ACTIVE_STATUSES)).filter(
                started_at__lt=running_cutoff
            ) | AgentRun.objects.filter(
                status=RunStatus.QUEUED, queued_at__lt=queued_cutoff
            )
            for run in stale.distinct():
                run.finalize(
                    RunStatus.FAILED,
                    error_type="WorkerLost",
                    error_message=(
                        "The run was reaped: no worker completed it. Check that a "
                        "Celery worker is consuming the agent_mode queue."
                    ),
                )
                reaped += 1
        except Exception:  # noqa: BLE001
            logger.exception("agent_mode: sweep failed for %s", tenant.name)
    return {"reaped": reaped}


@shared_task(name="zango.agent_mode.prune_agent_artifacts")
def prune_agent_artifacts() -> dict:
    """Keep snapshots bounded and drop very old event rows.

    Snapshots are whole-workspace tarballs, so without pruning they grow
    without limit. Events are the other unbounded table — a chatty 20-minute
    run emits thousands of rows.
    """
    from datetime import timedelta

    from django.conf import settings as dj
    from django.db import connection as conn

    from zango.apps.shared.tenancy.models import TenantModel

    from .models import AgentRunEvent
    from .snapshot import prune_snapshots

    keep = int(getattr(dj, "AGENT_MODE_SNAPSHOT_RETENTION", 5))
    cutoff = timezone.now() - timedelta(days=90)
    removed_snapshots = 0
    removed_events = 0

    for tenant in TenantModel.objects.exclude(schema_name="public"):
        runs_dir = os.path.join(str(dj.BASE_DIR), ".agent_mode", "runs", tenant.name)
        try:
            removed_snapshots += prune_snapshots(runs_dir, keep=keep)
        except Exception:  # noqa: BLE001
            logger.exception("agent_mode: snapshot prune failed for %s", tenant.name)
        try:
            conn.set_tenant(tenant)
            deleted, _ = AgentRunEvent.objects.filter(ts__lt=cutoff).delete()
            removed_events += deleted
        except Exception:  # noqa: BLE001
            logger.exception("agent_mode: event prune failed for %s", tenant.name)

    return {"snapshots_removed": removed_snapshots, "events_removed": removed_events}


@shared_task(bind=True, name="zango.agent_mode.agent_requirement_turn")
def agent_requirement_turn(self, requirement_uuid: str, tenant_name: str) -> dict:
    """One conversational turn of phase 1.

    Short by design: the analyst reads a little and replies. The session is
    resumed each turn, so a conversation can span hours of human thinking
    without any worker being held open.
    """
    from zango.apps.shared.tenancy.models import TenantModel

    from .context import build_app_context
    from .credentials import resolve_credentials
    from .models import (
        AgentRequirement,
        MessageRole,
    )
    from .requirements import (
        build_analyst_options,
        compose_analyst_prompt,
    )
    from .stream import AgentStream

    creds = resolve_credentials()  # public schema, before set_tenant
    tenant = TenantModel.objects.get(name=tenant_name)
    connection.set_tenant(tenant)

    try:
        req = AgentRequirement.objects.get(object_uuid=requirement_uuid)
    except AgentRequirement.DoesNotExist:
        return {"status": "missing"}

    def _finish(**fields):
        req.is_thinking = False
        for key, value in fields.items():
            setattr(req, key, value)
        req.save(update_fields=[*fields, "is_thinking", "modified_at"])

    if not creds.is_usable:
        _finish(error_message="No Anthropic credential is configured.")
        return {"status": "no_credentials"}

    last_user = req.messages.filter(role=MessageRole.USER).order_by("-seq").first()
    if last_user is None:
        _finish(error_message="No user message to respond to.")
        return {"status": "empty"}

    text_parts: list[str] = []
    session_id = ""
    cost = None
    stream = None
    try:
        ctx = build_app_context(tenant)
        prompt = compose_analyst_prompt(req, ctx, last_user.content)
        stream = AgentStream(options=None, prompt=prompt)
        stream.options = build_analyst_options(ctx=ctx, creds=creds, requirement=req)

        for item in stream:
            if item.kind == "message":
                message = item.payload
                name = type(message).__name__
                if name == "AssistantMessage":
                    for block in getattr(message, "content", None) or []:
                        if type(block).__name__ == "TextBlock":
                            text_parts.append(getattr(block, "text", "") or "")
                elif name == "SystemMessage":
                    data = getattr(message, "data", None) or {}
                    session_id = session_id or data.get("session_id") or ""
                elif name == "ResultMessage":
                    session_id = getattr(message, "session_id", "") or session_id
                    cost = getattr(message, "total_cost_usd", None)
            elif item.kind == "error":
                raise item.payload
            elif item.kind == "done":
                break
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent_mode: requirement turn failed")
        _finish(error_message=f"{type(exc).__name__}: {exc}"[:2000])
        return {"status": "failed"}
    finally:
        if stream is not None:
            stream.request_stop()
            stream.join(timeout=10)

    try:
        return _record_analyst_reply(req, text_parts, session_id, cost)
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent_mode: could not record the analyst reply")
        _finish(error_message=f"{type(exc).__name__}: {exc}"[:2000])
        return {"status": "failed"}


def _record_analyst_reply(req, text_parts, session_id, cost) -> dict:
    """Persist one analyst reply. Separated so the caller can guarantee that
    `is_thinking` is always cleared, whatever goes wrong in here."""
    from decimal import Decimal

    from .models import AgentRequirementMessage, MessageRole, RequirementStatus
    from .requirements import (
        derive_title,
        extract_questions,
        extract_spec,
        looks_like_question,
        strip_fences,
    )

    reply = "\n\n".join(part for part in text_parts if part.strip()).strip()
    spec = extract_spec(reply)
    questions = extract_questions(reply)
    conversational = strip_fences(reply) or (
        "I've drafted the requirement — review it on the right."
        if spec
        else "A few questions before I write this up."
        if questions
        else "(no reply)"
    )

    next_seq = (
        req.messages.order_by("-seq").values_list("seq", flat=True).first() or 0
    ) + 1
    AgentRequirementMessage.objects.create(
        requirement=req,
        seq=next_seq,
        role=MessageRole.ASSISTANT,
        content=conversational,
        questions=questions,
        is_question=bool(questions)
        or (looks_like_question(conversational) and not spec),
    )

    req.turns += 1
    if session_id:
        req.session_id = session_id[:128]
    if cost is not None:
        # ResultMessage.total_cost_usd is a float; the column round-trips as
        # Decimal. Adding the two raises, so normalise before accumulating —
        # it only shows up from the second turn onwards.
        req.total_cost_usd = (req.total_cost_usd or Decimal("0")) + Decimal(str(cost))
    if spec:
        req.record_spec(spec)
        # The title starts life as the opening ask truncated to 80 characters
        # — a sentence, not a name, and the panel shows it as the app's name.
        # The spec's own heading is that name, so it always wins once there is
        # one. (`derive_title` falls back to what we had if the spec has no
        # heading, so this can never blank it.)
        req.title = derive_title(spec, req.title or req.initial_prompt)
        # Only advance out of gathering; never regress an approved spec.
        if req.status == RequirementStatus.GATHERING:
            req.status = RequirementStatus.READY

    req.is_thinking = False
    req.error_message = ""
    req.save()
    return {
        "status": req.status,
        "spec": bool(spec),
        "questions": len(questions),
        "turns": req.turns,
    }


@shared_task(bind=True, name="zango.agent_mode.agent_app_scaffold")
def agent_app_scaffold(self, scaffold_uuid: str) -> dict:
    """Name and launch the app behind a "Build with Agent" ask.

    Stays on the public schema throughout: it reads platform settings, writes
    a public-schema scaffold row and creates a tenant. The workspace itself is
    built by ``initialize_workspace``, which this task only kicks off — the
    panel polls for that separately, so no worker is held open for it.
    """
    from zango.apps.shared.agent_mode.models import AgentAppScaffold

    from .scaffold import launch_app

    try:
        scaffold = AgentAppScaffold.objects.get(object_uuid=scaffold_uuid)
    except AgentAppScaffold.DoesNotExist:
        return {"status": "missing"}

    try:
        launch_app(scaffold)
    except Exception as exc:  # noqa: BLE001 - the user is watching a spinner
        logger.exception("agent_mode: could not launch the app for a scaffold")
        scaffold.fail(f"{type(exc).__name__}: {exc}")
        return {"status": "failed"}

    return {"status": scaffold.status, "app_name": scaffold.app_name}
