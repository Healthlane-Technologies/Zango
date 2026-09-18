"""Build with Agent — turn a one-line ask into an app with a live requirement.

The existing Agent Mode flow assumes an app: its requirement conversation
lives in the tenant schema and its analyst reads the tenant's workspace. This
module covers the step before that, for a user who has no app yet:

    ask -> name it -> launch the app -> open a requirement inside it

Only the first two steps are new. Once the requirement exists, the user is
handed to the ordinary Agent Mode chat and nothing downstream knows the app
was minutes old.

Every stage is resumable from the ``AgentAppScaffold`` row, because app
creation takes long enough that a browser reload during it is routine.
"""

from __future__ import annotations

import json
import logging

from django.db import IntegrityError


logger = logging.getLogger("zango.agent_mode")


# Mirrors the "Deployed"/"Failed"/"Staged" vocabulary the platform app list
# already polls with, so the panel has one state machine to learn.
APP_PENDING = "pending"
APP_READY = "ready"
APP_FAILED = "failed"


def _tenant_for(scaffold):
    from zango.apps.shared.tenancy.models import TenantModel

    if not scaffold.app_uuid:
        return None
    return TenantModel.objects.filter(uuid=scaffold.app_uuid).first()


def _init_task_outcome(task_id: str) -> tuple[str, str]:
    """(outcome, error) for a workspace-init task: "success"/"failure"/"".

    ``initialize_workspace`` catches its own exceptions and returns
    ``{"result": "failure", "error": ...}`` from a task Celery still records
    as SUCCESS, so the Celery status alone cannot tell a finished launch from
    a broken one — the payload has to be read. "" means "not finished yet".
    """
    try:
        from django_celery_results.models import TaskResult

        row = (
            TaskResult.objects.filter(task_id=task_id)
            .only("status", "result")
            .first()
        )
    except Exception:  # noqa: BLE001 - a missing result is just "pending"
        logger.exception("agent_mode: could not read the workspace init result")
        return "", ""

    if row is None:
        return "", ""
    if row.status == "FAILURE":
        return "failure", (row.result or "")[:2000]
    if row.status != "SUCCESS":
        return "", ""

    try:
        payload = json.loads(row.result) if row.result else {}
    except (TypeError, ValueError):
        payload = {}
    if isinstance(payload, dict) and payload.get("result") == "failure":
        return "failure", str(payload.get("error") or "")[:2000]
    return "success", ""


def app_creation_state(scaffold) -> tuple[str, str]:
    """Where the app itself has got to, and why if it failed.

    The Celery result is authoritative when it exists: a launch that died
    partway leaves the tenant row on "staged" forever, which reads
    identically to one still in progress.
    """
    tenant = _tenant_for(scaffold)
    if tenant is None:
        return APP_PENDING, ""
    if tenant.status in ("suspended", "deleted"):
        return APP_FAILED, f"The app was {tenant.status} before it finished launching."

    if scaffold.init_task_id:
        outcome, error = _init_task_outcome(scaffold.init_task_id)
        if outcome == "failure":
            return APP_FAILED, error
        if outcome == "success":
            return APP_READY, ""

    return (APP_READY, "") if tenant.status == "deployed" else (APP_PENDING, "")


def launch_app(scaffold) -> None:
    """Name the app, then create it. Runs on the public schema.

    Idempotent by status: a retried task that finds the scaffold past
    ``naming`` leaves the existing app alone rather than creating a second.
    """
    from zango.apps.shared.agent_mode.models import ScaffoldStatus
    from zango.apps.shared.tenancy.models import TenantModel

    from .config import load_config
    from .credentials import resolve_credentials
    from .naming import suggest_identity, unique_name

    if scaffold.status != ScaffoldStatus.NAMING or scaffold.app_uuid:
        return

    cfg = load_config()
    if not cfg.enabled:
        scaffold.fail("Build with AI is disabled for this platform.")
        return

    creds = resolve_credentials()
    identity = suggest_identity(scaffold.prompt, creds)
    name = unique_name(identity.name)

    # unique_name reads the table, so two launches racing on the same stem can
    # both pick it; the unique constraint is what actually decides.
    app = init_task_id = None
    for attempt in range(3):
        try:
            app, init_task_id = TenantModel.create(
                name=name,
                schema_name=name,
                description=identity.description or scaffold.prompt[:500],
                app_template_name=None,
                tenant_type="app",
                status="staged",
            )
            break
        except IntegrityError:
            if attempt == 2:
                raise
            logger.warning("agent_mode: app name '%s' was taken; retrying", name)
            # The winner is committed by now, so the next read sees it and
            # picks the next free suffix.
            name = unique_name(identity.name)

    scaffold.app_name = name
    scaffold.app_label = identity.label or name
    scaffold.app_description = identity.description
    scaffold.name_source = identity.source
    scaffold.app_uuid = app.uuid
    scaffold.init_task_id = (init_task_id or "")[:64]
    scaffold.status = ScaffoldStatus.CREATING
    scaffold.error_message = ""
    scaffold.save(
        update_fields=[
            "app_name",
            "app_label",
            "app_description",
            "name_source",
            "app_uuid",
            "init_task_id",
            "status",
            "error_message",
            "modified_at",
        ]
    )
    logger.info(
        "agent_mode: scaffold %s launched app '%s' (%s)",
        scaffold.object_uuid,
        name,
        identity.source,
    )


def handoff_requirement(scaffold):
    """Open the requirement conversation inside the new app.

    Returns ``(requirement_uuid, tenant)``. Idempotent: a scaffold that
    already carries a requirement returns it rather than starting a second
    conversation about the same ask.
    """
    from django_tenants.utils import schema_context

    from django.db import transaction

    from zango.apps.shared.agent_mode.models import ScaffoldStatus

    from .models import AgentRequirement, AgentRequirementMessage, MessageRole

    tenant = _tenant_for(scaffold)
    if tenant is None:
        raise RuntimeError("The app has not been created yet.")
    if scaffold.requirement_uuid:
        return str(scaffold.requirement_uuid), tenant

    with schema_context(tenant.schema_name):
        requirement = AgentRequirement.objects.create(
            initial_prompt=scaffold.prompt,
            title=scaffold.prompt[:80],
            created_by_label=scaffold.created_by_label,
            is_thinking=True,
        )
        AgentRequirementMessage.objects.create(
            requirement=requirement,
            seq=1,
            role=MessageRole.USER,
            content=scaffold.prompt,
        )

    # Back on the public schema: the scaffold row lives there.
    scaffold.requirement_uuid = requirement.object_uuid
    scaffold.status = ScaffoldStatus.READY
    scaffold.error_message = ""
    scaffold.save(
        update_fields=["requirement_uuid", "status", "error_message", "modified_at"]
    )

    # ATOMIC_REQUESTS wraps the calling view, so nothing above is visible to a
    # worker yet. Dispatching now would race the rows' visibility.
    transaction.on_commit(lambda: _dispatch_first_turn(requirement, tenant))
    return str(requirement.object_uuid), tenant


def _dispatch_first_turn(requirement, tenant) -> None:
    """Queue the analyst's opening turn, once the requirement is committed."""
    from django_tenants.utils import schema_context

    from django.conf import settings as dj

    from .models import AgentRequirement
    from .tasks import agent_requirement_turn

    try:
        result = agent_requirement_turn.apply_async(
            args=[str(requirement.object_uuid), tenant.name],
            queue=getattr(dj, "AGENT_MODE_QUEUE", "") or None,
            soft_time_limit=600,
            time_limit=660,
        )
    except Exception:  # noqa: BLE001
        logger.exception("agent_mode: could not queue the first analyst turn")
        # Leaving is_thinking set would hang the chat on "Thinking…" forever.
        with schema_context(tenant.schema_name):
            AgentRequirement.objects.filter(pk=requirement.pk).update(
                is_thinking=False,
                error_message=(
                    "The agent could not be reached. Send your message again."
                ),
            )
        return

    with schema_context(tenant.schema_name):
        AgentRequirement.objects.filter(pk=requirement.pk).update(
            celery_task_id=(result.id or "")[:64]
        )


def state_payload(scaffold) -> dict:
    """Everything the chat page needs to render one poll."""
    if scaffold.requirement_uuid:
        app_state, app_error = APP_READY, ""
    elif scaffold.app_uuid:
        app_state, app_error = app_creation_state(scaffold)
    else:
        app_state, app_error = APP_PENDING, ""

    return {
        "uuid": str(scaffold.object_uuid),
        "status": scaffold.status,
        "prompt": scaffold.prompt,
        "app_uuid": str(scaffold.app_uuid) if scaffold.app_uuid else None,
        "app_name": scaffold.app_name,
        "app_label": scaffold.app_label or scaffold.app_name,
        "app_description": scaffold.app_description,
        "name_source": scaffold.name_source,
        "app_state": app_state,
        "requirement_uuid": (
            str(scaffold.requirement_uuid) if scaffold.requirement_uuid else None
        ),
        # The scaffold's own error when it has one; otherwise whatever the
        # workspace build reported, so a failure is never just a dead spinner.
        "error_message": scaffold.error_message or app_error,
        "created_at": scaffold.created_at.isoformat() if scaffold.created_at else None,
    }
