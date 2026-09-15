"""Platform API views for Agent Mode.

Mounted under /api/v1/apps/<app_uuid>/agent-mode/.

Mirrors the code_execution API: `set_app_schema_path` binds the tenant from
the URL, responses go through `get_api_response`, and the event tail uses the
same `after_seq` / `is_terminal` contract the panel already knows how to poll.
"""

from __future__ import annotations

import logging

from django.db import IntegrityError, connection, transaction
from django.utils.decorators import method_decorator
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from zango.apps.agent_mode.models import (
    RUN_PHASE_ORDER,
    TERMINAL_STATUSES,
    AgentRequirement,
    AgentRun,
    AgentRunEvent,
    RunStatus,
    TriggerKind,
)
from zango.core.api import (
    TenantMixin,
    ZangoGenericPlatformAPIView,
    get_api_response,
)
from zango.core.api.utils import ZangoAPIPagination
from zango.core.common_utils import set_app_schema_path

from .serializers import (
    AgentRequirementDetailSerializer,
    AgentRequirementListSerializer,
    AgentRunCreateSerializer,
    AgentRunDetailSerializer,
    AgentRunListSerializer,
)


log = logging.getLogger(__name__)


def _in_tenant(tenant):
    """Re-enter the tenant schema.

    `on_commit` callbacks run *after* the view returns, by which point
    `set_app_schema_path`'s `schema_context` has already restored `public`.
    Touching a TENANT_APPS table there fails with UndefinedTable — the row is
    committed, the task is queued, and only the callback blows up, so it
    surfaces as a 500 on an operation that actually succeeded.
    """
    from django_tenants.utils import schema_context

    return schema_context(tenant.schema_name)


def _bind_tenant(view, app_uuid):
    tenant = view.get_tenant(app_uuid=app_uuid)
    connection.set_tenant(tenant)
    return tenant


def _iso(value):
    """datetime -> ISO string.

    `get_api_response` does a bare `json.dumps()`, so a raw datetime in a
    hand-built payload raises "Object of type datetime is not JSON
    serializable". DRF serializers cover the other endpoints; this one
    assembles its response manually.
    """
    return value.isoformat() if value is not None else None


def _user_label(request) -> str:
    user = getattr(request, "user", None)
    return (getattr(user, "email", "") or str(user or ""))[:255]


@method_decorator(set_app_schema_path, name="dispatch")
class AgentModeAvailabilityView(ZangoGenericPlatformAPIView, TenantMixin):
    """GET availability/ — drives whether the App Settings CTA renders."""

    def get(self, request, app_uuid, *args, **kwargs):
        from zango.apps.agent_mode.availability import probe

        try:
            tenant = _bind_tenant(self, app_uuid)
            payload = probe(tenant)
            in_flight = (
                AgentRun.objects.exclude(status__in=list(TERMINAL_STATUSES))
                .order_by("-queued_at")
                .first()
            )
            payload["in_flight_run"] = (
                {
                    "uuid": str(in_flight.object_uuid),
                    "status": in_flight.status,
                    "started_at": _iso(in_flight.started_at),
                }
                if in_flight
                else None
            )
            last = AgentRun.objects.order_by("-queued_at").first()
            payload["last_run"] = (
                {
                    "uuid": str(last.object_uuid),
                    "status": last.status,
                    "ended_at": _iso(last.ended_at),
                    "requires_restart": last.requires_restart,
                }
                if last
                else None
            )
            return get_api_response(True, payload, 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: availability probe failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentRunListCreateView(
    ZangoGenericPlatformAPIView, TenantMixin, ZangoAPIPagination
):
    """GET runs/ — history.  POST runs/ — start a run."""

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            qs = AgentRun.objects.all()
            status_filter = request.GET.get("status")
            if status_filter:
                qs = qs.filter(status=status_filter)
            search = request.GET.get("search")
            if search:
                qs = qs.filter(prompt__icontains=search)
            paginated = self.paginate_queryset(qs, request, view=self)
            serializer = AgentRunListSerializer(paginated, many=True)
            return get_api_response(
                True,
                {"runs": self.get_paginated_response_data(serializer.data)},
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: run list failed")
            return get_api_response(False, {"message": str(exc)}, 500)

    def post(self, request, app_uuid, *args, **kwargs):
        from django.conf import settings as dj

        from zango.apps.agent_mode.availability import probe
        from zango.apps.agent_mode.tasks import agent_run_executor

        try:
            tenant = _bind_tenant(self, app_uuid)

            status_probe = probe(tenant)
            if not status_probe["available"]:
                return get_api_response(
                    False,
                    {
                        "message": "Agent Mode is not available for this app.",
                        "reasons": status_probe["reasons"],
                        "checks": status_probe["checks"],
                    },
                    409,
                )

            # A run is normally built from an approved requirement; a raw
            # prompt is still accepted for one-off work.
            requirement = None
            requirement_uuid = request.data.get("requirement_uuid")
            if requirement_uuid:
                requirement = AgentRequirement.objects.filter(
                    object_uuid=requirement_uuid
                ).first()
                if requirement is None:
                    return get_api_response(
                        False, {"message": "requirement not found"}, 404
                    )
                if not requirement.can_build:
                    return get_api_response(
                        False,
                        {
                            "message": (
                                "This requirement must be approved before it "
                                "can be built."
                            ),
                            "status": requirement.status,
                        },
                        409,
                    )
                data = dict(request.data)
                data["prompt"] = requirement.spec_markdown
                serializer = AgentRunCreateSerializer(data=data)
            else:
                serializer = AgentRunCreateSerializer(data=request.data)

            if not serializer.is_valid():
                return get_api_response(False, {"errors": serializer.errors}, 400)
            payload = serializer.validated_data

            in_flight = (
                AgentRun.objects.exclude(status__in=list(TERMINAL_STATUSES))
                .order_by("-queued_at")
                .first()
            )
            if in_flight is not None:
                return get_api_response(
                    False,
                    {
                        "message": "A run is already in progress for this app.",
                        "run_uuid": str(in_flight.object_uuid),
                        "status": in_flight.status,
                    },
                    409,
                )

            prompt = payload["prompt"]
            max_seconds = int(getattr(dj, "AGENT_MODE_MAX_RUN_SECONDS", 1800))

            try:
                with transaction.atomic():
                    run = AgentRun.objects.create(
                        prompt=prompt,
                        title=(requirement.title if requirement else prompt[:80])[:255],
                        requirement=requirement,
                        trigger_kind=TriggerKind.UI,
                        triggered_by=_user_label(request),
                        status=RunStatus.QUEUED,
                        is_active=True,
                        model=payload.get("model")
                        or getattr(dj, "AGENT_MODE_MODEL", ""),
                        effort=payload.get("effort")
                        or getattr(dj, "AGENT_MODE_EFFORT", ""),
                        permission_mode=getattr(
                            dj, "AGENT_MODE_PERMISSION_MODE", "acceptEdits"
                        ),
                        max_turns=payload.get("max_turns")
                        or (getattr(dj, "AGENT_MODE_MAX_TURNS", 0) or None),
                        max_budget_usd=payload.get("max_budget_usd")
                        or getattr(dj, "AGENT_MODE_MAX_BUDGET_USD", None),
                    )
            except IntegrityError:
                # The partial unique index is the real guard; the check above
                # is only UX and can lose a race.
                return get_api_response(
                    False,
                    {"message": "A run is already in progress for this app."},
                    409,
                )

            def _dispatch():
                # After commit: ATOMIC_REQUESTS wraps the view, and the worker
                # polls the broker within milliseconds — dispatching inside the
                # transaction races the row's visibility.
                result = agent_run_executor.apply_async(
                    args=[str(run.object_uuid), tenant.name],
                    queue=getattr(dj, "AGENT_MODE_QUEUE", "") or None,
                    soft_time_limit=max_seconds,
                    time_limit=max_seconds + 300,
                )
                with _in_tenant(tenant):
                    AgentRun.objects.filter(pk=run.pk).update(
                        celery_task_id=(result.id or "")[:64]
                    )

            transaction.on_commit(_dispatch)

            return get_api_response(
                True,
                {"uuid": str(run.object_uuid), "status": run.status},
                201,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: run create failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentRunDetailView(ZangoGenericPlatformAPIView, TenantMixin):
    """GET runs/{uuid}/"""

    def get(self, request, app_uuid, run_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                run = AgentRun.objects.get(object_uuid=run_uuid)
            except AgentRun.DoesNotExist:
                return get_api_response(False, {"message": "run not found"}, 404)
            data = AgentRunDetailSerializer(run).data
            if run.requires_restart:
                data["restart_hint"] = (
                    "Model, task or settings files changed. Restart the app "
                    "server and any Celery workers to load the new code."
                )
            return get_api_response(True, data, 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: run detail failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentRunEventTailView(ZangoGenericPlatformAPIView, TenantMixin):
    """GET runs/{uuid}/event-tail/

    Forward tail: ?after_seq=N -> events with seq > N, ascending.
    Backward page: ?before_seq=N&limit=M -> the latest M with seq < N, also
    ascending so the client can prepend.

    `is_terminal` tells the client when to stop polling.
    """

    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 500
    FIELDS = (
        "seq",
        "ts",
        "kind",
        "phase",
        "level",
        "message",
        "tool_name",
        "tool_use_id",
        "parent_tool_use_id",
        "is_error",
        "data",
    )

    def get(self, request, app_uuid, run_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                run = AgentRun.objects.only(
                    "id", "status", "total_cost_usd", "num_turns"
                ).get(object_uuid=run_uuid)
            except AgentRun.DoesNotExist:
                return get_api_response(False, {"message": "run not found"}, 404)

            try:
                limit = min(
                    self.MAX_PAGE_SIZE,
                    max(1, int(request.GET.get("limit", self.DEFAULT_PAGE_SIZE))),
                )
            except (TypeError, ValueError):
                limit = self.DEFAULT_PAGE_SIZE

            base = AgentRunEvent.objects.filter(run_id=run.id)
            total = base.count()
            before_raw = request.GET.get("before_seq")

            if before_raw is not None:
                try:
                    before_seq = int(before_raw)
                except (TypeError, ValueError):
                    before_seq = 0
                events = list(
                    base.filter(seq__lt=before_seq)
                    .order_by("-seq")
                    .values(*self.FIELDS)[:limit]
                )
                events.reverse()
            else:
                try:
                    after_seq = int(request.GET.get("after_seq", 0))
                except (TypeError, ValueError):
                    after_seq = 0
                events = list(
                    base.filter(seq__gt=after_seq)
                    .order_by("seq")
                    .values(*self.FIELDS)[:limit]
                )

            for row in events:
                ts = row.get("ts")
                row["ts"] = ts.isoformat() if ts else None

            oldest = events[0]["seq"] if events else None
            newest = events[-1]["seq"] if events else None
            is_terminal = run.status in TERMINAL_STATUSES

            return get_api_response(
                True,
                {
                    "status": run.status,
                    "is_terminal": is_terminal,
                    # Coarse stage for the progress timeline. Derived from the
                    # newest event so it survives page reloads mid-run.
                    "phase": (
                        "done"
                        if is_terminal
                        else (
                            AgentRunEvent.objects.filter(run_id=run.id)
                            .order_by("-seq")
                            .values_list("phase", flat=True)
                            .first()
                            or "preparing"
                        )
                    ),
                    "phase_order": list(RUN_PHASE_ORDER),
                    "events": events,
                    # Alias so the existing log-tail client shape also works.
                    "lines": events,
                    "oldest_seq": oldest,
                    "newest_seq": newest,
                    "total": total,
                    "has_more_before": bool(oldest and oldest > 1),
                    "next_seq": newest,
                    "progress": {
                        "turns": run.num_turns,
                        "cost_usd": str(run.total_cost_usd)
                        if run.total_cost_usd is not None
                        else None,
                    },
                },
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: event tail failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentRunAbortView(ZangoGenericPlatformAPIView, TenantMixin):
    """POST runs/{uuid}/abort/ — cooperative first, revoke as a fallback."""

    def post(self, request, app_uuid, run_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                run = AgentRun.objects.get(object_uuid=run_uuid)
            except AgentRun.DoesNotExist:
                return get_api_response(False, {"message": "run not found"}, 404)

            if run.is_terminal:
                return get_api_response(
                    True, {"status": run.status, "message": "already finished"}, 200
                )

            run.abort_requested = True
            run.save(update_fields=["abort_requested", "modified_at"])

            # Note the correct FK kwarg: the analogous line in the
            # code_execution abort view passes `execution_uuid=`, which is not
            # a field, so its TypeError is swallowed and the row never lands.
            try:
                last = (
                    AgentRunEvent.objects.filter(run_id=run.id)
                    .order_by("-seq")
                    .values_list("seq", flat=True)
                    .first()
                )
                AgentRunEvent.objects.create(
                    run=run,
                    seq=(last or 0) + 1,
                    kind="sys",
                    level="warn",
                    message=f"Abort requested by {_user_label(request)}.",
                )
            except Exception:  # noqa: BLE001
                log.exception("agent_mode: failed to record abort event")

            return get_api_response(
                True,
                {"status": run.status, "abort_requested": True},
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: abort failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentRunResumeView(ZangoGenericPlatformAPIView, TenantMixin):
    """POST runs/{uuid}/resume/ — continue an interrupted run.

    A build that stops partway — exhausted API credits, a tripped budget, a
    timeout, an aborted run — leaves real work on disk. Starting over throws
    it away and pays for it twice. Resuming reuses the SDK session, so the
    agent continues with its own context rather than rediscovering the
    workspace.

    Forks the session rather than continuing it in place, so the failed run's
    transcript stays intact and a resume can itself be resumed.
    """

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    # A successful run has nothing to continue.
    RESUMABLE = {"failed", "timeout", "aborted", "partial"}

    def post(self, request, app_uuid, run_uuid, *args, **kwargs):
        from django.conf import settings as dj

        from zango.apps.agent_mode.availability import probe
        from zango.apps.agent_mode.tasks import agent_run_executor

        try:
            tenant = _bind_tenant(self, app_uuid)
            try:
                previous = AgentRun.objects.get(object_uuid=run_uuid)
            except AgentRun.DoesNotExist:
                return get_api_response(False, {"message": "run not found"}, 404)

            if not previous.is_terminal:
                return get_api_response(
                    False, {"message": "That run is still going."}, 409
                )
            if previous.status not in self.RESUMABLE:
                return get_api_response(
                    False,
                    {"message": (f"A {previous.status} run has nothing to resume.")},
                    409,
                )
            if not previous.session_id:
                return get_api_response(
                    False,
                    {
                        "message": (
                            "This run has no agent session recorded, so it "
                            "cannot be continued. Start a new build instead."
                        )
                    },
                    409,
                )

            status_probe = probe(tenant)
            if not status_probe["available"]:
                return get_api_response(
                    False,
                    {
                        "message": "Agent Mode is not available for this app.",
                        "reasons": status_probe["reasons"],
                    },
                    409,
                )

            in_flight = (
                AgentRun.objects.exclude(status__in=list(TERMINAL_STATUSES))
                .order_by("-queued_at")
                .first()
            )
            if in_flight is not None:
                return get_api_response(
                    False,
                    {
                        "message": "A run is already in progress for this app.",
                        "run_uuid": str(in_flight.object_uuid),
                    },
                    409,
                )

            max_seconds = int(getattr(dj, "AGENT_MODE_MAX_RUN_SECONDS", 1800))
            try:
                with transaction.atomic():
                    run = AgentRun.objects.create(
                        prompt=previous.prompt,
                        title=previous.title,
                        requirement=previous.requirement,
                        resumed_from=previous,
                        trigger_kind=TriggerKind.RESUME,
                        triggered_by=_user_label(request),
                        status=RunStatus.QUEUED,
                        is_active=True,
                        model=previous.model,
                        effort=previous.effort,
                        permission_mode=previous.permission_mode,
                        max_turns=previous.max_turns,
                        max_budget_usd=previous.max_budget_usd
                        or getattr(dj, "AGENT_MODE_MAX_BUDGET_USD", None),
                    )
            except IntegrityError:
                return get_api_response(
                    False,
                    {"message": "A run is already in progress for this app."},
                    409,
                )

            def _dispatch():
                result = agent_run_executor.apply_async(
                    args=[str(run.object_uuid), tenant.name],
                    queue=getattr(dj, "AGENT_MODE_QUEUE", "") or None,
                    soft_time_limit=max_seconds,
                    time_limit=max_seconds + 300,
                )
                with _in_tenant(tenant):
                    AgentRun.objects.filter(pk=run.pk).update(
                        celery_task_id=(result.id or "")[:64]
                    )

            transaction.on_commit(_dispatch)
            return get_api_response(
                True,
                {
                    "uuid": str(run.object_uuid),
                    "status": run.status,
                    "resumed_from": str(previous.object_uuid),
                },
                201,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: resume failed")
            return get_api_response(False, {"message": str(exc)}, 500)


# ---------------------------------------------------------------------------
# Phase 1 — requirement gathering
# ---------------------------------------------------------------------------


def _dispatch_turn(requirement, tenant):
    """Queue one analyst turn after the outer transaction commits."""
    from django.conf import settings as dj

    from zango.apps.agent_mode.tasks import agent_requirement_turn

    def _go():
        result = agent_requirement_turn.apply_async(
            args=[str(requirement.object_uuid), tenant.name],
            queue=getattr(dj, "AGENT_MODE_QUEUE", "") or None,
            soft_time_limit=600,
            time_limit=660,
        )
        with _in_tenant(tenant):
            AgentRequirement.objects.filter(pk=requirement.pk).update(
                celery_task_id=(result.id or "")[:64]
            )

    transaction.on_commit(_go)


def _append_user_message(requirement, content: str):
    from zango.apps.agent_mode.models import AgentRequirementMessage, MessageRole

    next_seq = (
        requirement.messages.order_by("-seq").values_list("seq", flat=True).first() or 0
    ) + 1
    return AgentRequirementMessage.objects.create(
        requirement=requirement,
        seq=next_seq,
        role=MessageRole.USER,
        content=content,
    )


@method_decorator(set_app_schema_path, name="dispatch")
class AgentRequirementListCreateView(
    ZangoGenericPlatformAPIView, TenantMixin, ZangoAPIPagination
):
    """GET requirements/ — history.  POST requirements/ — start gathering."""

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            qs = AgentRequirement.objects.all()
            status_filter = request.GET.get("status")
            if status_filter:
                qs = qs.filter(status=status_filter)
            paginated = self.paginate_queryset(qs, request, view=self)
            data = AgentRequirementListSerializer(paginated, many=True).data
            return get_api_response(
                True, {"requirements": self.get_paginated_response_data(data)}, 200
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: requirement list failed")
            return get_api_response(False, {"message": str(exc)}, 500)

    def post(self, request, app_uuid, *args, **kwargs):
        from zango.apps.agent_mode.availability import probe
        from zango.apps.agent_mode.requirements import MAX_MESSAGE_CHARS

        try:
            tenant = _bind_tenant(self, app_uuid)
            status_probe = probe(tenant)
            if not status_probe["available"]:
                return get_api_response(
                    False,
                    {
                        "message": "Agent Mode is not available for this app.",
                        "reasons": status_probe["reasons"],
                    },
                    409,
                )

            prompt = (request.data.get("prompt") or "").strip()
            if not prompt:
                return get_api_response(
                    False, {"message": "Describe what you want to build."}, 400
                )
            if len(prompt) > MAX_MESSAGE_CHARS:
                return get_api_response(
                    False, {"message": "That description is too long."}, 400
                )

            with transaction.atomic():
                requirement = AgentRequirement.objects.create(
                    initial_prompt=prompt,
                    title=prompt[:80],
                    created_by_label=_user_label(request),
                    is_thinking=True,
                )
                _append_user_message(requirement, prompt)

            _dispatch_turn(requirement, tenant)
            return get_api_response(
                True,
                {"uuid": str(requirement.object_uuid), "status": requirement.status},
                201,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: requirement create failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentRequirementDetailView(ZangoGenericPlatformAPIView, TenantMixin):
    """GET requirements/{uuid}/ — the conversation, spec and status."""

    def get(self, request, app_uuid, requirement_uuid, *args, **kwargs):
        try:
            _bind_tenant(self, app_uuid)
            try:
                requirement = AgentRequirement.objects.get(object_uuid=requirement_uuid)
            except AgentRequirement.DoesNotExist:
                return get_api_response(False, {"message": "not found"}, 404)
            return get_api_response(
                True, AgentRequirementDetailSerializer(requirement).data, 200
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: requirement detail failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentRequirementMessageView(ZangoGenericPlatformAPIView, TenantMixin):
    """POST requirements/{uuid}/messages/ — reply and get another turn."""

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, app_uuid, requirement_uuid, *args, **kwargs):
        from zango.apps.agent_mode.requirements import MAX_MESSAGE_CHARS

        try:
            tenant = _bind_tenant(self, app_uuid)
            try:
                requirement = AgentRequirement.objects.get(object_uuid=requirement_uuid)
            except AgentRequirement.DoesNotExist:
                return get_api_response(False, {"message": "not found"}, 404)

            if not requirement.is_open:
                return get_api_response(
                    False,
                    {"message": f"This requirement is {requirement.status}."},
                    409,
                )
            if requirement.is_thinking:
                return get_api_response(
                    False, {"message": "The agent is still replying."}, 409
                )

            content = (request.data.get("content") or "").strip()
            if not content:
                return get_api_response(False, {"message": "Message is empty."}, 400)
            if len(content) > MAX_MESSAGE_CHARS:
                return get_api_response(False, {"message": "Message too long."}, 400)

            with transaction.atomic():
                _append_user_message(requirement, content)
                requirement.is_thinking = True
                requirement.error_message = ""
                requirement.save(
                    update_fields=["is_thinking", "error_message", "modified_at"]
                )

            _dispatch_turn(requirement, tenant)
            return get_api_response(True, {"status": requirement.status}, 202)
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: requirement message failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentRequirementSpecView(ZangoGenericPlatformAPIView, TenantMixin):
    """POST requirements/{uuid}/spec/ — the user edits the spec directly.

    Faster than another agent turn for a small correction, and every revision
    is versioned so nothing is lost.
    """

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, app_uuid, requirement_uuid, *args, **kwargs):
        from zango.apps.agent_mode.models import RequirementStatus, SpecSource

        try:
            _bind_tenant(self, app_uuid)
            try:
                requirement = AgentRequirement.objects.get(object_uuid=requirement_uuid)
            except AgentRequirement.DoesNotExist:
                return get_api_response(False, {"message": "not found"}, 404)
            if requirement.status == RequirementStatus.APPROVED:
                return get_api_response(
                    False,
                    {"message": "This requirement is already approved."},
                    409,
                )

            markdown = (request.data.get("spec_markdown") or "").strip()
            if not markdown:
                return get_api_response(False, {"message": "Spec is empty."}, 400)

            requirement.record_spec(markdown, source=SpecSource.USER)
            if requirement.status == RequirementStatus.GATHERING:
                requirement.status = RequirementStatus.READY
            requirement.save()
            return get_api_response(
                True,
                {
                    "spec_version": requirement.spec_version,
                    "status": requirement.status,
                },
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: spec edit failed")
            return get_api_response(False, {"message": str(exc)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentRequirementApproveView(ZangoGenericPlatformAPIView, TenantMixin):
    """POST requirements/{uuid}/approve/ — lock the spec and enable building."""

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, app_uuid, requirement_uuid, *args, **kwargs):
        from django.utils import timezone

        from zango.apps.agent_mode.models import RequirementStatus

        try:
            _bind_tenant(self, app_uuid)
            try:
                requirement = AgentRequirement.objects.get(object_uuid=requirement_uuid)
            except AgentRequirement.DoesNotExist:
                return get_api_response(False, {"message": "not found"}, 404)

            if not requirement.spec_markdown.strip():
                return get_api_response(
                    False,
                    {"message": "There is no specification to approve yet."},
                    400,
                )

            requirement.status = RequirementStatus.APPROVED
            requirement.approved_at = timezone.now()
            requirement.approved_by = _user_label(request)
            requirement.save(
                update_fields=[
                    "status",
                    "approved_at",
                    "approved_by",
                    "modified_at",
                ]
            )
            return get_api_response(
                True,
                {"status": requirement.status, "can_build": requirement.can_build},
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agent_mode: approve failed")
            return get_api_response(False, {"message": str(exc)}, 500)
