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

from .requirements import roles_from_yaml_spec


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
    roles heading, so ordinary prose cannot conjure a role. A spec with no such
    section may still be a template journey, which names its roles in YAML.
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
    return names or roles_from_yaml_spec(spec)


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
            name: {"messages": count} for name, count in state["models_seen"].items()
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
                "configure Agent Mode settings (with AGENT_MODE_AUTH=subscription: "
                "set CLAUDE_CODE_OAUTH_TOKEN, and DEBUG must be on)."
            ),
        )
        return {"status": run.status}

    run.status = RunStatus.RUNNING
    run.started_at = timezone.now()
    run.celery_task_id = (self.request.id or "")[:64]
    run.save(update_fields=["status", "started_at", "celery_task_id", "modified_at"])

    return _execute(run, tenant, creds, workspaces_root(), build_app_context)


def _build_ask(run, template_build) -> str:
    """What the build is asked to do: the stored prompt, or the template build request."""
    if template_build is None:
        return run.prompt
    from zango.apps.shared.app_templates.models import AppTemplateVersion

    from .prompt import template_build_request

    version = AppTemplateVersion.objects.filter(
        object_uuid=template_build.template.version_uuid
    ).first()
    engine_paths = (
        list(version.workspace_engine_paths or [])
        if version and version.has_workspace
        else []
    )
    return template_build_request(
        template_build.template, template_build.spec_path, engine_paths
    )


def _execute(run, tenant, creds, ws_root, build_app_context) -> dict:
    from django.conf import settings as dj

    from .models import (  # noqa: F401
        RUN_PHASE_ORDER,
        EventKind,
        EventLevel,
        RunPhase,
        RunStatus,
    )
    from .options import build_agent_options
    from .postrun import requires_restart, run_step
    from .prompt import compose_prompt, compose_resume_prompt
    from .recorder import EventRecorder
    from .settings_writer import write_run_settings
    from .snapshot import create_snapshot, diff_manifest, workspace_manifest
    from .stream import AgentStream
    from .studio_build import (
        StudioBuild,
        StudioError,
        fix_rounds,
        is_studio,
        service_account,
    )

    recorder = EventRecorder(run)
    template_build = None
    studio = None
    levels = {"sys": EventLevel.SYS, "warn": EventLevel.WARN, "err": EventLevel.ERR}

    def _studio_emit(kind, message, *, level="info", is_error=False, data=None):
        recorder.emit(
            kind,
            message,
            level=levels.get(level, EventLevel.INFO),
            is_error=is_error,
            data=data,
        )
        recorder.flush_if_stale(0.5)

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
        # Template builds: engine restored, journey on disk, template skill.
        from .template_build import prepare as prepare_template_build

        template_build = prepare_template_build(run, ctx.workspace_path, run_dir)
        if template_build is None or not template_build.skill:
            # Every app is written in a template's YAML spec (from scratch: the
            # generic Zango app spec) and built with that template's skill.
            raise StudioError(
                "NoAppSpec",
                "This requirement has no app spec to build from. Start a new "
                "requirement: it is written as an app spec and built from it.",
            )
        skill = template_build.skill
        run.workspace_path = ctx.workspace_path[:1024]
        run.skill_name = skill[:128]
        update = ["workspace_path", "skill_name", "modified_at"]
        if template_build is not None:
            run.spec_path = template_build.spec_path[:1024]
            run.template_version_uuid = template_build.template.version_uuid or None
            update += ["spec_path", "template_version_uuid"]
        run.save(update_fields=update)
        if template_build is not None:
            recorder.emit(
                EventKind.SYS,
                f"Building on the {template_build.template.name} template "
                f"v{template_build.template.version}; the approved journey is at "
                f"{template_build.spec_path}",
                level=EventLevel.SYS,
            )
            if template_build.restored:
                recorder.emit(
                    EventKind.SYS,
                    f"Restored {len(template_build.restored)} engine file(s) that did not "
                    "match the template: "
                    + ", ".join(p for p, _ in template_build.restored[:10]),
                    level=EventLevel.WARN,
                )

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

        # App Studio builds: the platform runs the skill's own scripts first
        # (spec check, runtime, frontend prep); the agent then writes code.
        if is_studio(template_build):
            recorder.set_phase(RunPhase.PREPARING)
            studio = StudioBuild.for_run(template_build, ctx, run_dir)
            # The platform half after the agent needs the app's build account.
            # Exercise it now (create, scope to the app, disable): a database
            # problem then fails here in a second, not after a finished agent pass.
            with service_account(tenant, emit=_studio_emit):
                pass
            try:
                requirement = getattr(run, "requirement", None)
                studio.prepare(
                    emit=_studio_emit,
                    template=template_build.template,
                    # Open mode: the approved prototype, for .zas/bundle/prototype/.
                    prototype=(
                        dict(requirement.prototype_parts or {})
                        if requirement is not None
                        and requirement.preview_mode == "open"
                        else None
                    ),
                )
            finally:
                run.post_steps = [r.to_dict() for r in studio.steps]
                run.save(update_fields=["post_steps", "modified_at"])
            # Re-baseline: the runtime and frontend files are the platform's,
            # not the agent's.
            baseline_manifest = workspace_manifest(ctx.workspace_path)

        # Create any roles the spec names *before* the agent runs. AppBuilder's
        # create_config resolves a role by primary key, so a role that does not
        # exist yet has no ID for the agent to pass — the first successful run
        # registered routes but no menus for exactly this reason.
        spec_roles = [] if studio is not None else _roles_from_text(run.prompt)
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
            if studio is not None:
                from .prompt import RESUME_PREAMBLE, compose_studio_prompt

                prompt = RESUME_PREAMBLE.format(reason=reason) + compose_studio_prompt(
                    ctx, template_build, studio
                )
            else:
                prompt = compose_resume_prompt(
                    _build_ask(run, template_build), ctx, reason, skill=skill
                )
            recorder.emit(
                EventKind.SYS,
                f"Resuming run {str(previous.object_uuid)[:8]} "
                f"({previous.status}). Continuing, not restarting.",
                level=EventLevel.SYS,
            )
        elif studio is not None:
            from .prompt import compose_studio_prompt

            prompt = compose_studio_prompt(ctx, template_build, studio)
        else:
            prompt = compose_prompt(_build_ask(run, template_build), ctx, skill=skill)
        stream = AgentStream(options=None, prompt=prompt)
        stream.options = build_agent_options(
            run=run,
            ctx=ctx,
            creds=creds,
            settings_path=settings_path,
            hook_sink=stream.hook_sink,
            stderr_sink=recorder.emit_stderr,
            template_build=template_build,
        )

        def _drive(agent_stream, run_state) -> dict:
            return _drive_stream(agent_stream, run_state, run=run, recorder=recorder)

        extra = _drive(stream, state)

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

            if studio is not None:
                status, extra = _finish_studio(
                    run=run,
                    tenant=tenant,
                    studio=studio,
                    state=state,
                    recorder=recorder,
                    emit=_studio_emit,
                    drive=_drive,
                    new_stream=lambda digest: _resume_stream(
                        digest,
                        run,
                        ctx,
                        creds,
                        settings_path,
                        template_build,
                        state,
                        agent_cfg,
                        recorder,
                    ),
                    baseline_manifest=baseline_manifest,
                    service_account=service_account,
                    rounds=fix_rounds(),
                )
            else:
                status, extra = _finish_classic(
                    run=run, tenant=tenant, ctx=ctx, changes=changes, recorder=recorder
                )

    except StudioError as exc:
        status = RunStatus.FAILED
        extra = {"error_type": exc.error_type[:128], "error_message": str(exc)[:8000]}
        recorder.emit(
            EventKind.ERROR,
            f"{exc.error_type}: {str(exc)[:2000]}",
            level=EventLevel.ERR,
            is_error=True,
        )
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
        if status != RunStatus.WAITING:
            recorder.set_phase(RunPhase.DONE)
        if stream is not None:
            stream.request_stop()
            stream.join(timeout=15)
        try:
            _apply_state(run, state)
        except Exception:  # noqa: BLE001
            logger.exception("agent_mode: failed to apply run state")
        recorder.flush()

    return _conclude(run, status, extra, recorder)


def _conclude(run, status, extra, recorder) -> dict:
    """Finalize the run — or park it, when the build is waiting for the user."""
    from .models import RunStatus

    if status == RunStatus.WAITING:
        run.pause(
            extra.get("pending_actions") or [], extra.get("studio_checkpoint") or {}
        )
    else:
        run.finalize(status, **extra)
    return {"status": run.status, "events": recorder.seq}


def _drive_stream(agent_stream, run_state, *, run, recorder) -> dict:
    """Run one agent stream to its end; returns error fields, or {}."""
    from .mapper import record_message
    from .models import EventKind, EventLevel

    failure: dict = {}
    last_abort_check = 0.0
    stopping = False
    for item in agent_stream:
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
            record_message(item.payload, recorder, run_state)
            recorder.flush_if_stale()
        elif item.kind == "done":
            break
        elif item.kind == "error":
            exc = item.payload
            failure = {
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
            if not stopping and _abort_requested(run.pk):
                stopping = True
                recorder.emit(
                    EventKind.SYS,
                    "Abort requested — interrupting the agent.",
                    level=EventLevel.WARN,
                )
                recorder.flush()
                agent_stream.request_stop()

    return failure


def _finish_classic(*, run, tenant, ctx, changes, recorder):
    """After a classic build: roles, test users, migrations and sync. (status, extra)."""
    from django.conf import settings as dj

    from .models import EventKind, EventLevel, RunPhase, RunStatus
    from .postrun import run_post_steps
    from .roles import ensure_roles
    from .users import ensure_users

    extra: dict = {}
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
    return status, extra


# A fix round resumes the build's session, and the resumed session's ResultMessage
# reports cost, tokens and API time as running totals for the whole session, so
# the fix round's figures already include the build's. Adding them counted the
# build again on every round (a $7 build was recorded as $38). Turns are per query.
_SESSION_TOTALS = (
    "total_cost_usd",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_creation_tokens",
    "duration_api_ms",
)


def _merge_state(state: dict, more: dict) -> None:
    """Fold a fix round's usage into the run's totals; the run keeps its first session."""
    for key in _SESSION_TOTALS:
        if more.get(key) is not None:
            state[key] = max(state.get(key) or 0, more[key])
    if more.get("model_usage"):
        state["model_usage"] = more["model_usage"]
    if more.get("num_turns") is not None:
        state["num_turns"] = (state.get("num_turns") or 0) + more["num_turns"]
    counts = dict(state.get("tool_use_counts") or {})
    for name, n in (more.get("tool_use_counts") or {}).items():
        counts[name] = counts.get(name, 0) + n
    state["tool_use_counts"] = counts
    if more.get("session_id") and not state.get("session_id"):
        state["session_id"] = more["session_id"]


def _resume_stream(
    digest, run, ctx, creds, settings_path, template_build, state, agent_cfg, recorder
):
    """An agent stream resuming the build's session with a fix-round digest, or None.

    None when there is no session to resume or the run's budget is spent: the
    ceiling covers the build and its fix rounds together.
    """
    from .models import EventKind, EventLevel
    from .options import build_agent_options
    from .stream import AgentStream

    session_id = state.get("session_id") or ""
    if not session_id:
        recorder.emit(
            EventKind.SYS,
            "No agent session to resume for a fix round.",
            level=EventLevel.WARN,
        )
        return None
    budget = float(run.max_budget_usd or getattr(agent_cfg, "max_budget_usd", 0) or 0)
    spent = float(state.get("total_cost_usd") or 0)
    if budget and spent >= budget:
        recorder.emit(
            EventKind.SYS,
            f"The run's budget (${budget:.2f}) is spent; no fix round.",
            level=EventLevel.WARN,
        )
        return None
    stream = AgentStream(options=None, prompt=digest)
    options = build_agent_options(
        run=run,
        ctx=ctx,
        creds=creds,
        settings_path=settings_path,
        hook_sink=stream.hook_sink,
        stderr_sink=recorder.emit_stderr,
        template_build=template_build,
    )
    options.resume = session_id
    options.fork_session = False
    if budget:
        options.max_budget_usd = round(budget - spent, 4)
    stream.options = options
    return stream


def _finish_studio(
    *,
    run,
    tenant,
    studio,
    state,
    recorder,
    emit,
    drive,
    new_stream,
    baseline_manifest,
    service_account,
    rounds,
    checkpoint=None,
    skip=False,
    prior_steps=(),
):
    """After an App Studio build's agent turn: the platform's half of the skill. (status, extra).

    ``checkpoint`` continues a build that paused for the user (``skip``:
    without the checks it was waiting to run); ``prior_steps`` are the steps
    recorded before the pause. The status is WAITING when the build pauses.
    """
    from .models import EventKind, EventLevel, RunPhase, RunStatus
    from .postrun import requires_restart
    from .snapshot import diff_manifest, workspace_manifest

    recorder.set_phase(RunPhase.APPLYING)

    def resume_agent(digest: str) -> bool:
        if _abort_requested(run.pk):
            return False
        stream = new_stream(digest)
        if stream is None:
            return False
        recorder.set_phase(RunPhase.BUILDING)
        fix_state: dict = {}
        try:
            failure = drive(stream, fix_state)
        finally:
            stream.request_stop()
            stream.join(timeout=15)
            _merge_state(state, fix_state)
            recorder.set_phase(RunPhase.APPLYING)
        return not failure and not fix_state.get("is_error")

    more = {"checkpoint": checkpoint, "skip": skip} if checkpoint is not None else {}
    try:
        with service_account(tenant, emit=emit) as platform_creds:
            outcome = studio.finish(
                platform_creds,
                resume_agent=resume_agent,
                rounds=rounds,
                emit=emit,
                **more,
            )
    finally:
        run.post_steps = [*prior_steps, *(r.to_dict() for r in studio.steps)]
        run.save(update_fields=["post_steps", "modified_at"])

    if baseline_manifest is not None:
        changes = diff_manifest(baseline_manifest, workspace_manifest(studio.workspace))
        run.files_changed = changes.to_dict()
        run.requires_restart = requires_restart(changes)
    run.test_users = studio.test_users() or None
    skipped = [
        {"layer": name, "reason": layer.reason}
        for name, layer in outcome.layers.items()
        if layer.status == "skip"
    ]
    # Skipped checks are never presented as passed: the run says what it could not verify.
    not_verified = [s["layer"] for s in skipped]
    run.studio_report = {
        "ok": outcome.ok,
        "bring_up_ok": outcome.bring_up_ok,
        "frontend": studio.frontend_ready,
        "frontend_reason": "" if studio.frontend_ready else studio.frontend_reason,
        "not_verified": not_verified,
        "rounds": outcome.rounds,
        "layers": {name: layer.to_dict() for name, layer in outcome.layers.items()},
        "skipped": skipped,
        "report": outcome.report,
    }
    run.save(
        update_fields=[
            "files_changed",
            "requires_restart",
            "test_users",
            "studio_report",
            "modified_at",
        ]
    )

    if getattr(outcome, "waiting", False):
        # The worker is released; `continue` picks the build up from here.
        titles = "; ".join(a.get("title", "") for a in outcome.pending_actions)
        recorder.emit(
            EventKind.SYS,
            f"Waiting for you: {titles}. Everything that does not depend on it has run; "
            "the build continues from here when you say it is done.",
            level=EventLevel.WARN,
            data={"pending_actions": outcome.pending_actions},
        )
        saved = _save_baseline(studio.run_dir, baseline_manifest)
        return RunStatus.WAITING, {
            "pending_actions": outcome.pending_actions,
            "studio_checkpoint": {**(outcome.checkpoint or {}), "baseline": saved},
        }

    def counts(layer):
        c = layer.counts or {}
        return f"{c.get('pass', 0)} passed, {c.get('fail', 0)} failed, {c.get('skip', 0)} skipped"

    lines = [
        f"{name}: "
        + (f"skipped — {layer.reason}" if layer.status == "skip" else counts(layer))
        for name, layer in outcome.layers.items()
    ]
    recorder.emit(
        EventKind.SYS,
        "App Studio checks — "
        + "; ".join(lines)
        + (f". Fix rounds: {outcome.rounds}." if outcome.rounds else "."),
        # a passing build can still carry look-only gaps: keep those visible
        level=EventLevel.SYS if not outcome.failing else EventLevel.WARN,
        data=run.studio_report,
    )
    if outcome.report.get("html_path"):
        recorder.emit(
            EventKind.SYS,
            f"Build report: {outcome.report['html_path']}"
            + (
                f" (verdict: {outcome.report['verdict']})"
                if outcome.report.get("verdict")
                else ""
            ),
            level=EventLevel.SYS,
        )
    if not_verified:
        recorder.emit(
            EventKind.SYS,
            "Not verified: "
            + ", ".join(not_verified)
            + ". These checks were skipped, not passed — see the reasons above.",
            level=EventLevel.WARN,
        )

    if outcome.ok and not studio.frontend_ready:
        return RunStatus.PARTIAL, {
            "error_type": "StudioNoFrontend",
            "error_message": (
                "Built without a frontend: /app is not served ("
                + (studio.frontend_reason or "the frontend phase was skipped")
                + "). Enable AGENT_MODE_ALLOW_FRONTEND_BUILD with Node installed and build again."
            )[:8000],
        }
    if outcome.ok:
        return RunStatus.SUCCESS, {}
    if not outcome.bring_up_ok:
        failed = next((r for r in reversed(studio.steps) if r.ran and not r.ok), None)
        message = (
            f"The agent finished but the platform's bring-up step "
            f"{failed.step if failed else ''} failed"
            + (f" after {outcome.rounds} fix round(s)" if outcome.rounds else "")
            + ". The files are already written; restore the pre-run snapshot with "
            "`manage.py agent_mode_restore` if you need to roll back."
        )
        return RunStatus.PARTIAL, {
            "error_type": "StudioBringUpFailed",
            "error_message": message[:8000],
        }
    failing = outcome.failing
    message = (
        "The app was built and brought up, but these checks still fail"
        + (f" after {outcome.rounds} fix round(s)" if outcome.rounds else "")
        + ": "
        + ", ".join(
            f"{name} ({len(outcome.layers[name].failures)})" for name in failing
        )
        + ". See the build report for details."
    )
    return RunStatus.PARTIAL, {
        "error_type": "StudioChecksFailed",
        "error_message": message[:8000],
    }


def _save_baseline(run_dir: str, manifest) -> str:
    """Keep the pre-agent file manifest beside the run, so a continuation can still diff."""
    import json

    if manifest is None:
        return ""
    path = os.path.join(run_dir, "baseline_manifest.json")
    try:
        os.makedirs(run_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh)
    except Exception:  # noqa: BLE001 - the diff is a nicety, never worth failing a build
        logger.exception("agent_mode: could not save the baseline manifest")
        return ""
    return path


def _load_baseline(path: str):
    import json

    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return None


def _state_from_run(run) -> dict:
    """The stream state a continuation starts from: the run's session and its totals so far."""
    state = {
        "session_id": run.session_id or "",
        "result_subtype": run.result_subtype,
        "terminal_reason": run.terminal_reason,
        "result_text": run.result_text,
        "num_turns": run.num_turns,
        "duration_api_ms": run.duration_api_ms,
        "api_error_status": run.api_error_status,
        "tool_use_counts": dict(run.tool_use_counts or {}),
        "model_usage": run.model_usage,
    }
    if run.total_cost_usd is not None:
        state["total_cost_usd"] = float(run.total_cost_usd)
    for key in (
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_creation_tokens",
    ):
        if getattr(run, key) is not None:
            state[key] = getattr(run, key)
    return state


@shared_task(bind=True, name="zango.agent_mode.agent_run_continue")
def agent_run_continue(
    self, run_uuid: str, tenant_name: str, skip: bool = False
) -> dict:
    """Go on with an App Studio build that paused for the user.

    Runs only what the pause held back — the AppBuilder routes, the checks
    that need the app or a browser — then fix rounds (resuming the agent's
    session), the report and the usual outcome. ``skip`` finishes without
    them, recorded as skipped by the user.
    """
    from zango.apps.shared.tenancy.models import TenantModel

    from .context import build_app_context, workspaces_root
    from .credentials import resolve_credentials
    from .models import AgentRun, RunStatus

    creds = resolve_credentials()  # public-schema read, before set_tenant
    tenant = TenantModel.objects.get(name=tenant_name)
    connection.set_tenant(tenant)
    try:
        run = AgentRun.objects.get(object_uuid=run_uuid)
    except AgentRun.DoesNotExist:
        logger.error("agent_mode: run %s not found in %s", run_uuid, tenant_name)
        return {"status": "missing"}
    if run.status != RunStatus.SYNCING or not run.studio_checkpoint:
        return {"status": run.status}

    run.celery_task_id = (self.request.id or "")[:64]
    run.save(update_fields=["celery_task_id", "modified_at"])
    return _continue(
        run, tenant, creds, workspaces_root(), build_app_context, skip=skip
    )


def _continue(run, tenant, creds, ws_root, build_app_context, *, skip=False) -> dict:
    from django.conf import settings as dj

    from .config import load_config
    from .models import AgentRunEvent, EventKind, EventLevel, RunPhase, RunStatus
    from .recorder import EventRecorder
    from .settings_writer import write_run_settings
    from .studio_build import StudioBuild, StudioError, fix_rounds, service_account
    from .template_build import TemplateBuild

    checkpoint = dict(run.studio_checkpoint or {})
    last_seq = (
        AgentRunEvent.objects.filter(run_id=run.id)
        .order_by("-seq")
        .values_list("seq", flat=True)
        .first()
    ) or 0
    recorder = EventRecorder(run, start_seq=last_seq)
    recorder.set_phase(RunPhase.APPLYING)
    levels = {"sys": EventLevel.SYS, "warn": EventLevel.WARN, "err": EventLevel.ERR}

    def emit(kind, message, *, level="info", is_error=False, data=None):
        recorder.emit(
            kind,
            message,
            level=levels.get(level, EventLevel.INFO),
            is_error=is_error,
            data=data,
        )
        recorder.flush_if_stale(0.5)

    state = _state_from_run(run)
    status = RunStatus.FAILED
    extra: dict = {}
    try:
        ctx = build_app_context(tenant)
        studio = StudioBuild.from_checkpoint(checkpoint)
        recorder.emit(
            EventKind.SYS,
            "Continuing the build"
            + (
                " without the checks it was waiting to run."
                if skip
                else " from where it paused."
            ),
            level=EventLevel.SYS,
        )

        # Fix rounds resume the agent's session; that needs the same options a build has.
        requirement = getattr(run, "requirement", None)
        template = (
            requirement.template
            if requirement is not None and requirement.template_slug
            else None
        )
        template_build = (
            TemplateBuild(
                template=template, spec_path=run.spec_path or studio.spec_path
            )
            if template is not None
            else None
        )
        agent_cfg = load_config()
        settings_path = write_run_settings(
            run_dir=studio.run_dir,
            workspace_path=ctx.workspace_path,
            workspaces_root=ws_root,
            base_dir=str(dj.BASE_DIR),
            project_name=os.path.basename(str(dj.BASE_DIR)),
        )

        def new_stream(digest):
            if template_build is None:
                recorder.emit(
                    EventKind.SYS,
                    "The template behind this build no longer loads; no fix round.",
                    level=EventLevel.WARN,
                )
                return None
            return _resume_stream(
                digest,
                run,
                ctx,
                creds,
                settings_path,
                template_build,
                state,
                agent_cfg,
                recorder,
            )

        status, extra = _finish_studio(
            run=run,
            tenant=tenant,
            studio=studio,
            state=state,
            recorder=recorder,
            emit=emit,
            drive=lambda agent_stream, run_state: _drive_stream(
                agent_stream, run_state, run=run, recorder=recorder
            ),
            new_stream=new_stream,
            baseline_manifest=_load_baseline(checkpoint.get("baseline", "")),
            service_account=service_account,
            rounds=fix_rounds(),
            checkpoint=checkpoint,
            skip=skip,
            prior_steps=list(run.post_steps or []),
        )
    except StudioError as exc:
        status = RunStatus.FAILED
        extra = {"error_type": exc.error_type[:128], "error_message": str(exc)[:8000]}
        recorder.emit(
            EventKind.ERROR,
            f"{exc.error_type}: {str(exc)[:2000]}",
            level=EventLevel.ERR,
            is_error=True,
        )
    except SoftTimeLimitExceeded:
        status = RunStatus.TIMEOUT
        extra = {
            "error_type": "SoftTimeLimitExceeded",
            "error_message": "The run exceeded its time limit.",
        }
        recorder.emit(
            EventKind.ERROR, "Run timed out.", level=EventLevel.ERR, is_error=True
        )
    except Exception as exc:  # noqa: BLE001
        status = RunStatus.FAILED
        extra = {
            "error_type": type(exc).__name__[:128],
            "error_message": str(exc)[:8000],
            "error_traceback": traceback.format_exc()[:20000],
        }
        logger.exception("agent_mode: continuing run %s failed", run.object_uuid)
        recorder.emit(
            EventKind.ERROR,
            f"{type(exc).__name__}: {exc}",
            level=EventLevel.ERR,
            is_error=True,
        )
    finally:
        if status != RunStatus.WAITING:
            recorder.set_phase(RunPhase.DONE)
        try:
            _apply_state(run, state)
        except Exception:  # noqa: BLE001
            logger.exception("agent_mode: failed to apply run state")
        recorder.flush()

    return _conclude(run, status, extra, recorder)


@shared_task(name="zango.agent_mode.sweep_stuck_agent_runs")
def sweep_stuck_agent_runs() -> dict:
    """Reap runs whose worker died, and runs stranded with no worker at all."""
    from datetime import timedelta

    from django.db import connection as conn
    from django.db.models import Q

    from zango.apps.shared.tenancy.models import TenantModel

    from .config import load_config
    from .models import ACTIVE_STATUSES, AgentRun, RunStatus

    max_seconds = load_config().max_run_seconds
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

            # A stop nobody answered: the worker holding the run is gone.
            from .liveness import close_if_abandoned

            for stopping in AgentRun.objects.filter(
                abort_requested=True, status__in=list(ACTIVE_STATUSES)
            ):
                if close_if_abandoned(stopping, now=now):
                    reaped += 1

            # WAITING is not in ACTIVE_STATUSES: it has no worker and may sit
            # for as long as the user takes. A continued run is measured from
            # when it was picked up again, not from when it first started.
            stale = AgentRun.objects.filter(status__in=list(ACTIVE_STATUSES)).filter(
                Q(resumed_at__isnull=True, started_at__lt=running_cutoff)
                | Q(resumed_at__lt=running_cutoff)
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
    bench = None
    try:
        ctx = build_app_context(tenant)
        from .documents import attachment_note, write_docs_dir
        from .preview_focus import focus_note

        # The user's documents, where the analyst can read them.

        docs_path = write_docs_dir(tenant.name, req)
        prompt = compose_analyst_prompt(
            req,
            ctx,
            last_user.content
            + attachment_note(str(docs_path) if docs_path else "", req, last_user)
            + focus_note(last_user.preview_focus, _plain_spec(req)),
            docs_dir=str(docs_path) if docs_path else "",
        )
        stream = AgentStream(options=None, prompt=prompt)

        # Template requirements are edited through spec tools. The workbench
        # is built here, on the tenant-bound thread; its handlers run on the
        # pump and only hand accepted edits back through the stream.
        spec_server = None
        template = req.template if req.template_slug else None
        if template is not None and template.is_yaml:
            from .preview_probe import probe_for
            from .spec_tools import SpecWorkbench, build_spec_server

            proto = None
            if req.preview_mode == "open":
                from .prototype import PrototypeBench

                # Open mode: the analyst writes the prototype itself; the template's
                # kit preview and its sketch probe do not apply.
                # Uploaded HTML files, for proto_import (read here: the tools can't use the ORM).
                html_docs = {
                    d.name: bytes(d.data).decode("utf-8", "replace")
                    for d in req.documents.filter(content_type="text/html")
                }
                proto = PrototypeBench(
                    req.prototype_parts,
                    emit=lambda edit: stream.push("spec", edit),
                    documents=html_docs,
                )
            bench = SpecWorkbench(
                req.spec_markdown,
                template,
                emit=lambda edit: stream.push("spec", edit),
                flags=req.spec_flags,
                open_decisions=req.open_decisions,
                workflows=req.workflows,
                probe=None if proto is not None else probe_for(template),
                sketch_looks=req.sketch_looks,
                proto=proto,
            )
            spec_server = build_spec_server(bench)
        stream.options = build_analyst_options(
            ctx=ctx,
            creds=creds,
            requirement=req,
            spec_server=spec_server,
            docs_dir=str(docs_path) if docs_path else "",
            preview=bench is not None and bench.probe is not None,
        )

        for item in stream:
            if item.kind == "spec":
                _record_spec_edit(req, item.payload)
            elif item.kind == "message":
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
        if bench is not None:
            bench.close()  # the preview runner, if a check started one this turn

    try:
        return _record_analyst_reply(req, text_parts, session_id, cost, bench=bench)
    except Exception as exc:  # noqa: BLE001
        logger.exception("agent_mode: could not record the analyst reply")
        _finish(error_message=f"{type(exc).__name__}: {exc}"[:2000])
        return {"status": "failed"}


def _plain_spec(req):
    """The requirement's YAML spec as plain data, or None (not YAML, or broken)."""
    if not (req.spec_markdown or "").strip():
        return None
    from zango.apps.shared.app_templates.services.spec import yamlio

    try:
        doc = yamlio.load(req.spec_markdown)
    except yamlio.SpecYAMLError:
        return None
    return doc if isinstance(doc, dict) else None


def _record_spec_edit(req, edit: dict) -> None:
    """Save one spec-tool result straight away, so the panel sees it land.

    An edit carries the new YAML; a provenance call (spec_flag, spec_unflag,
    spec_open_decisions) carries only flags and open decisions,
    spec_set_workflows only the narrative workflows, and preview_look only
    which custom screens the analyst has seen.
    """
    edit = edit or {}
    fields = ["modified_at"]
    text = edit.get("yaml") or ""
    if text.strip():
        req.spec_markdown = text
        req.spec_is_draft = True
        req.draft_revision += 1
        req.changed_paths = list(edit.get("changed_paths") or [])
        req.validation_issues = list(edit.get("issues") or [])
        fields += [
            "spec_markdown",
            "spec_is_draft",
            "draft_revision",
            "changed_paths",
            "validation_issues",
        ]
    if "flags" in edit:
        req.spec_flags = list(edit["flags"])
        fields.append("spec_flags")
    if "open_decisions" in edit:
        req.open_decisions = list(edit["open_decisions"])
        fields.append("open_decisions")
    if "workflows" in edit:
        req.workflows = dict(edit["workflows"] or {})
        fields.append("workflows")
    if "sketch_looks" in edit:
        req.sketch_looks = dict(edit["sketch_looks"] or {})
        fields.append("sketch_looks")
    if "prototype_parts" in edit:
        req.prototype_parts = dict(edit["prototype_parts"] or {})
        req.prototype_hash = edit.get("prototype_hash") or ""
        req.prototype_revision += 1
        fields += ["prototype_parts", "prototype_hash", "prototype_revision"]
    if len(fields) > 1:
        req.save(update_fields=fields)


def _is_yaml_spec(text: str) -> bool:
    """Whether a fenced spec is a YAML document (a mapping), not prose."""
    if not (text or "").strip():
        return False
    from zango.apps.shared.app_templates.services.spec import yamlio

    try:
        return isinstance(yamlio.load(text), dict)
    except yamlio.SpecYAMLError:
        return False


def _start_template_draft(req) -> None:
    """The user just took the template the analyst offered.

    A YAML template starts from its starter spec — what the panel previews and
    the spec tools edit from the next turn on. Whatever was gathered before
    is in the conversation, and the next turn writes it in.
    """
    template = req.template
    if template is None or not template.is_yaml:
        return
    if not _is_yaml_spec(req.spec_markdown):
        req.spec_markdown = (template.starter_yaml or "").strip()
        req.spec_is_draft = True
        req.draft_revision += 1
    # The analyst's session predates the template: its next prompt carries
    # the template's instructions once (requirements.compose_analyst_prompt).
    req.mode = "adopted"


def _record_analyst_reply(req, text_parts, session_id, cost, bench=None) -> dict:
    """Persist one analyst reply. Separated so the caller can guarantee that
    `is_thinking` is always cleared, whatever goes wrong in here."""
    from decimal import Decimal

    from .models import AgentRequirementMessage, MessageRole, RequirementStatus
    from .requirements import (
        derive_title,
        extract_draft_spec,
        extract_questions,
        extract_spec,
        extract_template,
        looks_like_question,
        strip_fences,
    )

    reply = "\n\n".join(part for part in text_parts if part.strip()).strip()
    spec = extract_spec(reply)
    # Only meaningful while there is no finished spec: a draft emitted
    # alongside one is the same content, and the finished fence is the
    # authority.
    draft = "" if spec else extract_draft_spec(reply)
    template_slug = extract_template(reply)
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
    # Before the spec is recorded: the template decides the format, and the
    # version row stores the format it was written in.
    if req.mode == "adopted":
        req.mode = "interview"  # the template's instructions went out this turn
    if template_slug and req.adopt_template(template_slug):
        _start_template_draft(req)

    if req.spec_format == "yaml" and not (bench is not None and bench.edits):
        # A YAML template's spec is only ever YAML: the Markdown write-up an
        # analyst may still fence (it adopted the template this very turn,
        # before it had the spec tools) must not replace the journey.
        spec = spec if _is_yaml_spec(spec) else ""
        draft = draft if _is_yaml_spec(draft) else ""

    previous_spec = req.spec_markdown
    used_tools = bench is not None and (bench.edits or bench.ready_summary)
    if used_tools:
        # The tools already saved every edit as it happened; the fences, if
        # the model wrote any anyway, are not the authority.
        spec = draft = ""
        if bench.ready_summary and req.status == RequirementStatus.GATHERING:
            req.record_spec(bench.text)
            req.status = RequirementStatus.READY
        req.changed_paths = list(bench.changed)
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
    elif draft and req.status == RequirementStatus.GATHERING:
        # The interview is still running. The pane fills in so the user can
        # watch their app take shape, but the status does not move: there is
        # nothing to approve until the analyst says it is finished.
        req.record_draft_spec(draft)
        req.title = derive_title(draft, req.title or req.initial_prompt)

    if req.template_slug:
        from .template_spec import analyse

        # After tool edits the changed paths are already exact; only re-check.
        analyse(req, None if used_tools else previous_spec)

    req.is_thinking = False
    req.error_message = ""
    req.save()
    return {
        "status": req.status,
        "spec": bool(spec),
        "draft": bool(draft),
        "template": req.template_slug,
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
