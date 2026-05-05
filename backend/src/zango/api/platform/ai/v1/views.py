"""
REST API endpoints for the App Panel's AI provider management UI.
All endpoints are scoped to the current tenant (app).
Authentication: Session auth (platform admin user).
"""

from django.db import connection, transaction
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.decorators import method_decorator

from zango.ai.providers.registry import get_available_providers
from zango.apps.ai.models import (
    AppLLMAgent,
    AppLLMInvocation,
    AppLLMPrompt,
    AppLLMPromptVersion,
    AppLLMProvider,
    AppLLMTool,
)
from zango.core.api import ZangoGenericPlatformAPIView, get_api_response
from zango.core.api.utils import ZangoAPIPagination
from zango.core.common_utils import set_app_schema_path

from .serializers import (
    AppLLMAgentCreateSerializer,
    AppLLMAgentListSerializer,
    AppLLMAgentUpdateSerializer,
    AppLLMInvocationDetailSerializer,
    AppLLMInvocationListSerializer,
    AppLLMPromptCreateSerializer,
    AppLLMPromptDetailSerializer,
    AppLLMPromptListSerializer,
    AppLLMPromptUpdateSerializer,
    AppLLMPromptVersionCreateSerializer,
    AppLLMPromptVersionSerializer,
    AppLLMProviderCreateSerializer,
    AppLLMProviderListSerializer,
    AppLLMProviderUpdateSerializer,
    AppLLMToolDetailSerializer,
    AppLLMToolListSerializer,
)


@method_decorator(set_app_schema_path, name="dispatch")
class AvailableProvidersViewAPIV1(ZangoGenericPlatformAPIView):
    """
    GET /api/v1/apps/<app_uuid>/ai/providers/available/
    Returns metadata about all registered provider classes.
    Read from the PROVIDER_REGISTRY, not the database.
    """

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            providers = get_available_providers()
            return get_api_response(True, {"providers": providers}, 200)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class ProvidersListViewAPIV1(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    """
    GET  /api/v1/apps/<app_uuid>/ai/providers/
    POST /api/v1/apps/<app_uuid>/ai/providers/
    """

    pagination_class = ZangoAPIPagination

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            search = request.GET.get("search", "")
            providers = AppLLMProvider.objects.all().order_by("-id")

            if search:
                providers = providers.filter(
                    Q(name__icontains=search)
                    | Q(description__icontains=search)
                    | Q(provider_slug__icontains=search)
                )

            # Filter by status
            status_filter = request.GET.get("status")
            if status_filter == "active":
                providers = providers.filter(is_enabled=True)
            elif status_filter == "inactive":
                providers = providers.filter(is_enabled=False)

            paginated = self.paginate_queryset(providers, request, view=self)
            serializer = AppLLMProviderListSerializer(paginated, many=True)
            paginated_data = self.get_paginated_response_data(serializer.data)

            return get_api_response(
                True,
                {
                    "providers": paginated_data,
                    "message": "Providers fetched successfully",
                },
                200,
            )
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)

    def post(self, request, app_uuid, *args, **kwargs):
        try:
            serializer = AppLLMProviderCreateSerializer(data=request.data)
            if serializer.is_valid():
                provider = serializer.save()
                return get_api_response(
                    True,
                    {
                        "message": "Provider created successfully",
                        "provider_id": provider.id,
                    },
                    200,
                )
            else:
                error_messages = []
                for field_name, errors in serializer.errors.items():
                    for error in errors:
                        if isinstance(error, dict):
                            # Nested ValidationError dict e.g. {"config": "msg"}
                            for sub_field, sub_msg in error.items():
                                sub_msg_str = (
                                    sub_msg[0]
                                    if isinstance(sub_msg, list)
                                    else str(sub_msg)
                                )
                                error_messages.append(str(sub_msg_str))
                        else:
                            error_messages.append(str(error))
                return get_api_response(
                    False, {"message": ", ".join(error_messages)}, 400
                )
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class ProviderDetailViewAPIV1(ZangoGenericPlatformAPIView):
    """
    GET    /api/v1/apps/<app_uuid>/ai/providers/<provider_id>/
    PUT    /api/v1/apps/<app_uuid>/ai/providers/<provider_id>/
    DELETE /api/v1/apps/<app_uuid>/ai/providers/<provider_id>/
    """

    def get(self, request, app_uuid, provider_id, *args, **kwargs):
        try:
            provider = AppLLMProvider.objects.get(id=provider_id)
            serializer = AppLLMProviderListSerializer(provider)
            return get_api_response(True, {"provider": serializer.data}, 200)
        except AppLLMProvider.DoesNotExist:
            return get_api_response(False, {"message": "Provider not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)

    def put(self, request, app_uuid, provider_id, *args, **kwargs):
        try:
            provider = AppLLMProvider.objects.get(id=provider_id)
            serializer = AppLLMProviderUpdateSerializer(data=request.data)
            if serializer.is_valid():
                provider = serializer.update(provider, serializer.validated_data)
                result = AppLLMProviderListSerializer(provider)
                return get_api_response(
                    True,
                    {
                        "message": "Provider updated successfully",
                        "provider": result.data,
                    },
                    200,
                )
            else:
                error_messages = []
                for field_name, errors in serializer.errors.items():
                    for error in errors:
                        error_messages.append(f"{field_name}: {error}")
                return get_api_response(
                    False, {"message": ", ".join(error_messages)}, 400
                )
        except AppLLMProvider.DoesNotExist:
            return get_api_response(False, {"message": "Provider not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)

    def delete(self, request, app_uuid, provider_id, *args, **kwargs):
        try:
            provider = AppLLMProvider.objects.get(id=provider_id)
            if provider.total_invocations == 0:
                # Hard delete if no invocations
                provider.delete()
                return get_api_response(
                    True, {"message": "Provider deleted successfully"}, 200
                )
            else:
                # Soft delete: disable and rename
                provider.is_enabled = False
                provider.name = f"{provider.name} [deleted]"
                provider.save()
                return get_api_response(
                    True,
                    {"message": "Provider disabled (has invocation history)"},
                    200,
                )
        except AppLLMProvider.DoesNotExist:
            return get_api_response(False, {"message": "Provider not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class ProviderValidateViewAPIV1(ZangoGenericPlatformAPIView):
    """
    POST /api/v1/apps/<app_uuid>/ai/providers/<provider_id>/validate/
    Runs validate_config() against the provider.
    """

    def post(self, request, app_uuid, provider_id, *args, **kwargs):
        try:
            provider = AppLLMProvider.objects.get(id=provider_id)
            config = provider._decrypt_config()
            provider_cls = provider.get_provider_class()
            client = provider_cls(config)

            is_valid, error_msg = client.validate_config()

            provider.is_validated = is_valid
            provider.last_validated_at = timezone.now()
            provider.validation_error = error_msg if not is_valid else None
            provider.save()

            if is_valid:
                return get_api_response(
                    True,
                    {"message": "Provider credentials validated successfully"},
                    200,
                )
            else:
                return get_api_response(
                    False,
                    {"message": f"Validation failed: {error_msg}"},
                    400,
                )
        except AppLLMProvider.DoesNotExist:
            return get_api_response(False, {"message": "Provider not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class ProviderToggleViewAPIV1(ZangoGenericPlatformAPIView):
    """
    POST /api/v1/apps/<app_uuid>/ai/providers/<provider_id>/toggle/
    Enables or disables the provider.
    """

    def post(self, request, app_uuid, provider_id, *args, **kwargs):
        try:
            provider = AppLLMProvider.objects.get(id=provider_id)
            is_enabled = request.data.get("is_enabled")
            if is_enabled is None:
                return get_api_response(
                    False, {"message": "is_enabled field is required"}, 400
                )
            provider.is_enabled = bool(is_enabled)
            provider.save()
            status = "enabled" if provider.is_enabled else "disabled"
            return get_api_response(
                True, {"message": f"Provider {status} successfully"}, 200
            )
        except AppLLMProvider.DoesNotExist:
            return get_api_response(False, {"message": "Provider not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class ProviderUsageViewAPIV1(ZangoGenericPlatformAPIView):
    """
    GET /api/v1/apps/<app_uuid>/ai/providers/<provider_id>/usage/
    Returns usage/cost breakdown.
    """

    def get(self, request, app_uuid, provider_id, *args, **kwargs):
        try:
            provider = AppLLMProvider.objects.get(id=provider_id)

            # Per-model breakdown
            model_breakdown = (
                AppLLMInvocation.objects.filter(provider=provider, status="success")
                .values("model")
                .annotate(
                    total_invocations=Sum("id"),
                    total_input_tokens=Sum("input_tokens"),
                    total_output_tokens=Sum("output_tokens"),
                    total_cost=Sum("cost_usd"),
                )
                .order_by("-total_cost")
            )

            # Fix: use Count instead of Sum('id') for invocation count
            from django.db.models import Count

            model_breakdown = (
                AppLLMInvocation.objects.filter(provider=provider, status="success")
                .values("model")
                .annotate(
                    invocations=Count("id"),
                    input_tokens=Sum("input_tokens"),
                    output_tokens=Sum("output_tokens"),
                    cost=Sum("cost_usd"),
                )
                .order_by("-cost")
            )

            return get_api_response(
                True,
                {
                    "provider_id": provider.id,
                    "total_invocations": provider.total_invocations,
                    "total_input_tokens": provider.total_input_tokens,
                    "total_output_tokens": provider.total_output_tokens,
                    "total_cost_usd": str(provider.total_cost_usd),
                    "budget_status": provider.check_budget(),
                    "model_breakdown": [
                        {
                            **row,
                            "cost": str(row["cost"])
                            if row["cost"] is not None
                            else "0",
                        }
                        for row in model_breakdown
                    ],
                },
                200,
            )
        except AppLLMProvider.DoesNotExist:
            return get_api_response(False, {"message": "Provider not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class ProviderResetBudgetViewAPIV1(ZangoGenericPlatformAPIView):
    """
    POST /api/v1/apps/<app_uuid>/ai/providers/<provider_id>/reset-budget/
    Manually resets current_month_spend_usd to 0.
    """

    def post(self, request, app_uuid, provider_id, *args, **kwargs):
        try:
            provider = AppLLMProvider.objects.get(id=provider_id)
            provider.current_month_spend_usd = 0
            provider.last_budget_reset = timezone.now()
            provider.save()
            return get_api_response(True, {"message": "Budget reset successfully"}, 200)
        except AppLLMProvider.DoesNotExist:
            return get_api_response(False, {"message": "Provider not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class InvocationStatsViewAPIV1(ZangoGenericPlatformAPIView):
    """
    GET /api/v1/apps/<app_uuid>/ai/invocations/stats/
    Summary statistics for the invocation logs header.
    """

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            from datetime import timedelta

            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_24h = now - timedelta(hours=24)

            all_qs = AppLLMInvocation.objects.all()

            total_runs = all_qs.count()
            today_count = all_qs.filter(created_at__gte=today_start).count()
            errors_24h = (
                all_qs.filter(created_at__gte=cutoff_24h)
                .exclude(status="success")
                .count()
            )
            cost_today = (
                all_qs.filter(created_at__gte=today_start).aggregate(
                    total=Sum("cost_usd")
                )["total"]
                or 0
            )

            return get_api_response(
                True,
                {
                    "total_runs": total_runs,
                    "today": today_count,
                    "errors_24h": errors_24h,
                    "cost_today": str(cost_today),
                },
                200,
            )
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class InvocationListViewAPIV1(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    """
    GET /api/v1/apps/<app_uuid>/ai/invocations/
    Paginated list of invocation logs with filters.
    """

    pagination_class = ZangoAPIPagination

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            invocations = AppLLMInvocation.objects.all()

            # Filters
            search = request.GET.get("search", "")
            if search:
                invocations = invocations.filter(
                    Q(agent_name__icontains=search)
                    | Q(provider_name__icontains=search)
                    | Q(model__icontains=search)
                )

            provider_id = request.GET.get("provider_id")
            if provider_id:
                invocations = invocations.filter(provider_id=provider_id)

            agent_id = request.GET.get("agent_id")
            if agent_id:
                invocations = invocations.filter(agent_id=agent_id)

            status = request.GET.get("status")
            if status:
                invocations = invocations.filter(status=status)

            triggered_by = request.GET.get("triggered_by")
            if triggered_by:
                invocations = invocations.filter(triggered_by=triggered_by)

            model = request.GET.get("model")
            if model:
                invocations = invocations.filter(model=model)

            session_id = request.GET.get("session_id")
            if session_id:
                invocations = invocations.filter(session_id=session_id)

            paginated = self.paginate_queryset(invocations, request, view=self)
            serializer = AppLLMInvocationListSerializer(paginated, many=True)
            paginated_data = self.get_paginated_response_data(serializer.data)

            return get_api_response(
                True,
                {
                    "invocations": paginated_data,
                    "message": "Invocations fetched successfully",
                },
                200,
            )
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class InvocationDetailViewAPIV1(ZangoGenericPlatformAPIView):
    """
    GET /api/v1/apps/<app_uuid>/ai/invocations/<invocation_id>/
    Full invocation detail (audit drill-down).
    """

    def get(self, request, app_uuid, invocation_id, *args, **kwargs):
        try:
            invocation = AppLLMInvocation.objects.get(id=invocation_id)
            serializer = AppLLMInvocationDetailSerializer(invocation)
            return get_api_response(True, {"invocation": serializer.data}, 200)
        except AppLLMInvocation.DoesNotExist:
            return get_api_response(False, {"message": "Invocation not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


# ── Prompt Views ────────────────────────────────────────────────────────────


@method_decorator(set_app_schema_path, name="dispatch")
class PromptsListViewAPIV1(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    """
    GET  /api/v1/apps/<app_uuid>/ai/prompts/
    POST /api/v1/apps/<app_uuid>/ai/prompts/
    """

    pagination_class = ZangoAPIPagination

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            prompts = AppLLMPrompt.objects.select_related("active_version").all()

            search = request.GET.get("search", "")
            if search:
                prompts = prompts.filter(
                    Q(name__icontains=search) | Q(description__icontains=search)
                )

            type_filter = request.GET.get("type")
            if type_filter:
                prompts = prompts.filter(type=type_filter)

            # Summary stats
            total_prompts = AppLLMPrompt.objects.filter(is_active=True).count()
            total_versions = AppLLMPromptVersion.objects.count()
            active_versions = AppLLMPromptVersion.objects.filter(
                status="active"
            ).count()

            paginated = self.paginate_queryset(prompts, request, view=self)
            serializer = AppLLMPromptListSerializer(paginated, many=True)
            paginated_data = self.get_paginated_response_data(serializer.data)

            return get_api_response(
                True,
                {
                    "prompts": paginated_data,
                    "stats": {
                        "total_prompts": total_prompts,
                        "active_versions": active_versions,
                        "total_versions": total_versions,
                    },
                    "message": "Prompts fetched successfully",
                },
                200,
            )
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)

    def post(self, request, app_uuid, *args, **kwargs):
        try:
            serializer = AppLLMPromptCreateSerializer(data=request.data)
            if serializer.is_valid():
                prompt = serializer.save()
                return get_api_response(
                    True,
                    {
                        "message": "Prompt created successfully",
                        "prompt_id": prompt.id,
                    },
                    200,
                )
            else:
                error_messages = []
                for field_name, errors in serializer.errors.items():
                    for error in errors:
                        error_messages.append(f"{field_name}: {error}")
                return get_api_response(
                    False, {"message": ", ".join(error_messages)}, 400
                )
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class PromptDetailViewAPIV1(ZangoGenericPlatformAPIView):
    """
    GET    /api/v1/apps/<app_uuid>/ai/prompts/<prompt_id>/
    PUT    /api/v1/apps/<app_uuid>/ai/prompts/<prompt_id>/
    DELETE /api/v1/apps/<app_uuid>/ai/prompts/<prompt_id>/
    """

    def get(self, request, app_uuid, prompt_id, *args, **kwargs):
        try:
            prompt = AppLLMPrompt.objects.select_related("active_version").get(
                id=prompt_id
            )
            serializer = AppLLMPromptDetailSerializer(prompt)
            return get_api_response(True, {"prompt": serializer.data}, 200)
        except AppLLMPrompt.DoesNotExist:
            return get_api_response(False, {"message": "Prompt not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)

    def put(self, request, app_uuid, prompt_id, *args, **kwargs):
        try:
            prompt = AppLLMPrompt.objects.get(id=prompt_id)
            serializer = AppLLMPromptUpdateSerializer(data=request.data)
            if serializer.is_valid():
                prompt = serializer.update(prompt, serializer.validated_data)
                result = AppLLMPromptDetailSerializer(prompt)
                return get_api_response(
                    True,
                    {
                        "message": "Prompt updated successfully",
                        "prompt": result.data,
                    },
                    200,
                )
            else:
                error_messages = []
                for field_name, errors in serializer.errors.items():
                    for error in errors:
                        error_messages.append(f"{field_name}: {error}")
                return get_api_response(
                    False, {"message": ", ".join(error_messages)}, 400
                )
        except AppLLMPrompt.DoesNotExist:
            return get_api_response(False, {"message": "Prompt not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)

    def delete(self, request, app_uuid, prompt_id, *args, **kwargs):
        try:
            prompt = AppLLMPrompt.objects.get(id=prompt_id)
            if prompt.versions.exists():
                # Soft delete — preserve audit trail
                prompt.is_active = False
                prompt.save()
                return get_api_response(
                    True, {"message": "Prompt deactivated (has version history)"}, 200
                )
            else:
                prompt.delete()
                return get_api_response(
                    True, {"message": "Prompt deleted successfully"}, 200
                )
        except AppLLMPrompt.DoesNotExist:
            return get_api_response(False, {"message": "Prompt not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class PromptVersionsListViewAPIV1(ZangoGenericPlatformAPIView):
    """
    GET  /api/v1/apps/<app_uuid>/ai/prompts/<prompt_id>/versions/
    POST /api/v1/apps/<app_uuid>/ai/prompts/<prompt_id>/versions/
    """

    def get(self, request, app_uuid, prompt_id, *args, **kwargs):
        try:
            prompt = AppLLMPrompt.objects.get(id=prompt_id)
            versions = prompt.versions.all().order_by("-version_number")
            serializer = AppLLMPromptVersionSerializer(versions, many=True)
            return get_api_response(True, {"versions": serializer.data}, 200)
        except AppLLMPrompt.DoesNotExist:
            return get_api_response(False, {"message": "Prompt not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)

    def post(self, request, app_uuid, prompt_id, *args, **kwargs):
        try:
            prompt = AppLLMPrompt.objects.get(id=prompt_id)
            serializer = AppLLMPromptVersionCreateSerializer(
                data=request.data, context={"prompt": prompt}
            )
            if serializer.is_valid():
                version = serializer.save()
                result = AppLLMPromptVersionSerializer(version)
                return get_api_response(
                    True,
                    {
                        "message": f"Version v{version.version_number} created",
                        "version": result.data,
                    },
                    200,
                )
            else:
                error_messages = []
                for field_name, errors in serializer.errors.items():
                    for error in errors:
                        error_messages.append(f"{field_name}: {error}")
                return get_api_response(
                    False, {"message": ", ".join(error_messages)}, 400
                )
        except AppLLMPrompt.DoesNotExist:
            return get_api_response(False, {"message": "Prompt not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class PromptVersionDetailViewAPIV1(ZangoGenericPlatformAPIView):
    """
    GET /api/v1/apps/<app_uuid>/ai/prompts/<prompt_id>/versions/<version_id>/
    """

    def get(self, request, app_uuid, prompt_id, version_id, *args, **kwargs):
        try:
            version = AppLLMPromptVersion.objects.get(
                id=version_id, prompt_id=prompt_id
            )
            serializer = AppLLMPromptVersionSerializer(version)
            return get_api_response(True, {"version": serializer.data}, 200)
        except AppLLMPromptVersion.DoesNotExist:
            return get_api_response(False, {"message": "Version not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class PromptVersionPromoteViewAPIV1(ZangoGenericPlatformAPIView):
    """
    POST /api/v1/apps/<app_uuid>/ai/prompts/<prompt_id>/versions/<version_id>/promote/
    Promotes a version to active. Sets old active to inactive.
    """

    def post(self, request, app_uuid, prompt_id, version_id, *args, **kwargs):
        try:
            with transaction.atomic():
                prompt = AppLLMPrompt.objects.select_for_update().get(id=prompt_id)
                target_version = AppLLMPromptVersion.objects.get(
                    id=version_id, prompt=prompt
                )

                # Deactivate current active version
                if prompt.active_version_id:
                    AppLLMPromptVersion.objects.filter(
                        id=prompt.active_version_id
                    ).update(status="inactive")

                # Activate target version
                target_version.status = "active"
                target_version.save()

                # Update prompt's active_version pointer
                prompt.active_version = target_version
                prompt.save()

            return get_api_response(
                True,
                {
                    "message": f"Version v{target_version.version_number} promoted to active",
                },
                200,
            )
        except AppLLMPrompt.DoesNotExist:
            return get_api_response(False, {"message": "Prompt not found"}, 404)
        except AppLLMPromptVersion.DoesNotExist:
            return get_api_response(False, {"message": "Version not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class PromptCompareViewAPIV1(ZangoGenericPlatformAPIView):
    """
    GET /api/v1/apps/<app_uuid>/ai/prompts/<prompt_id>/compare/?v1=3&v2=4
    Returns both versions side-by-side for frontend diff rendering.
    """

    def get(self, request, app_uuid, prompt_id, *args, **kwargs):
        try:
            v1_num = request.GET.get("v1")
            v2_num = request.GET.get("v2")

            if not v1_num or not v2_num:
                return get_api_response(
                    False,
                    {"message": "Both v1 and v2 query parameters are required"},
                    400,
                )

            version_1 = AppLLMPromptVersion.objects.get(
                prompt_id=prompt_id, version_number=int(v1_num)
            )
            version_2 = AppLLMPromptVersion.objects.get(
                prompt_id=prompt_id, version_number=int(v2_num)
            )

            return get_api_response(
                True,
                {
                    "version_1": AppLLMPromptVersionSerializer(version_1).data,
                    "version_2": AppLLMPromptVersionSerializer(version_2).data,
                },
                200,
            )
        except AppLLMPromptVersion.DoesNotExist:
            return get_api_response(
                False, {"message": "One or both versions not found"}, 404
            )
        except (ValueError, TypeError):
            return get_api_response(
                False, {"message": "v1 and v2 must be valid version numbers"}, 400
            )
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


# ── Agent Views ─────────────────────────────────────────────────────────────


@method_decorator(set_app_schema_path, name="dispatch")
class AgentsListViewAPIV1(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    """
    GET  /api/v1/apps/<app_uuid>/ai/agents/
    POST /api/v1/apps/<app_uuid>/ai/agents/
    """

    pagination_class = ZangoAPIPagination

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            agents = AppLLMAgent.objects.select_related(
                "provider", "system_prompt", "user_prompt"
            ).all()

            search = request.GET.get("search", "")
            if search:
                agents = agents.filter(
                    Q(name__icontains=search) | Q(description__icontains=search)
                )

            status_filter = request.GET.get("status")
            if status_filter == "active":
                agents = agents.filter(is_enabled=True)
            elif status_filter == "disabled":
                agents = agents.filter(is_enabled=False)

            total_agents = AppLLMAgent.objects.count()
            active_agents = AppLLMAgent.objects.filter(is_enabled=True).count()

            paginated = self.paginate_queryset(agents, request, view=self)
            serializer = AppLLMAgentListSerializer(paginated, many=True)
            paginated_data = self.get_paginated_response_data(serializer.data)

            return get_api_response(
                True,
                {
                    "agents": paginated_data,
                    "stats": {
                        "total_agents": total_agents,
                        "active_agents": active_agents,
                    },
                    "message": "Agents fetched successfully",
                },
                200,
            )
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)

    def post(self, request, app_uuid, *args, **kwargs):
        try:
            serializer = AppLLMAgentCreateSerializer(data=request.data)
            if serializer.is_valid():
                agent = serializer.save()
                return get_api_response(
                    True,
                    {"message": "Agent created successfully", "agent_id": agent.id},
                    200,
                )
            else:
                error_messages = []
                for field_name, errors in serializer.errors.items():
                    for error in errors:
                        error_messages.append(f"{field_name}: {error}")
                return get_api_response(
                    False, {"message": ", ".join(error_messages)}, 400
                )
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentDetailViewAPIV1(ZangoGenericPlatformAPIView):
    """
    GET    /api/v1/apps/<app_uuid>/ai/agents/<agent_id>/
    PUT    /api/v1/apps/<app_uuid>/ai/agents/<agent_id>/
    DELETE /api/v1/apps/<app_uuid>/ai/agents/<agent_id>/
    """

    def get(self, request, app_uuid, agent_id, *args, **kwargs):
        try:
            agent = AppLLMAgent.objects.select_related(
                "provider", "system_prompt", "user_prompt"
            ).get(id=agent_id)
            serializer = AppLLMAgentListSerializer(agent)
            return get_api_response(True, {"agent": serializer.data}, 200)
        except AppLLMAgent.DoesNotExist:
            return get_api_response(False, {"message": "Agent not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)

    def put(self, request, app_uuid, agent_id, *args, **kwargs):
        try:
            agent = AppLLMAgent.objects.get(id=agent_id)
            serializer = AppLLMAgentUpdateSerializer(data=request.data)
            if serializer.is_valid():
                agent = serializer.update(agent, serializer.validated_data)
                result = AppLLMAgentListSerializer(agent)
                return get_api_response(
                    True,
                    {"message": "Agent updated successfully", "agent": result.data},
                    200,
                )
            else:
                error_messages = []
                for field_name, errors in serializer.errors.items():
                    for error in errors:
                        error_messages.append(f"{field_name}: {error}")
                return get_api_response(
                    False, {"message": ", ".join(error_messages)}, 400
                )
        except AppLLMAgent.DoesNotExist:
            return get_api_response(False, {"message": "Agent not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)

    def delete(self, request, app_uuid, agent_id, *args, **kwargs):
        try:
            agent = AppLLMAgent.objects.get(id=agent_id)
            if agent.total_invocations > 0:
                agent.is_enabled = False
                agent.name = f"{agent.name}-deleted"
                agent.save()
                return get_api_response(
                    True,
                    {"message": "Agent disabled (has invocation history)"},
                    200,
                )
            else:
                agent.delete()
                return get_api_response(
                    True, {"message": "Agent deleted successfully"}, 200
                )
        except AppLLMAgent.DoesNotExist:
            return get_api_response(False, {"message": "Agent not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentToggleViewAPIV1(ZangoGenericPlatformAPIView):
    """
    POST /api/v1/apps/<app_uuid>/ai/agents/<agent_id>/toggle/
    """

    def post(self, request, app_uuid, agent_id, *args, **kwargs):
        try:
            agent = AppLLMAgent.objects.get(id=agent_id)
            is_enabled = request.data.get("is_enabled")
            if is_enabled is None:
                return get_api_response(
                    False, {"message": "is_enabled field is required"}, 400
                )
            agent.is_enabled = bool(is_enabled)
            agent.save()
            status = "enabled" if agent.is_enabled else "disabled"
            return get_api_response(
                True, {"message": f"Agent {status} successfully"}, 200
            )
        except AppLLMAgent.DoesNotExist:
            return get_api_response(False, {"message": "Agent not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentDuplicateViewAPIV1(ZangoGenericPlatformAPIView):
    """
    POST /api/v1/apps/<app_uuid>/ai/agents/<agent_id>/duplicate/
    Creates a disabled copy with "-copy" suffix.
    """

    def post(self, request, app_uuid, agent_id, *args, **kwargs):
        try:
            original = AppLLMAgent.objects.get(id=agent_id)

            # Generate unique copy name
            copy_name = f"{original.name}-copy"
            counter = 1
            while AppLLMAgent.objects.filter(name=copy_name).exists():
                copy_name = f"{original.name}-copy-{counter}"
                counter += 1

            clone = AppLLMAgent.objects.create(
                name=copy_name,
                description=original.description,
                provider=original.provider,
                model=original.model,
                system_prompt=original.system_prompt,
                user_prompt=original.user_prompt,
                temperature=original.temperature,
                max_tokens=original.max_tokens,
                timeout_seconds=original.timeout_seconds,
                output_schema=original.output_schema,
                guardrails=original.guardrails,
                tools=original.tools,
                memory_enabled=original.memory_enabled,
                memory_max_messages=original.memory_max_messages,
                is_enabled=False,
            )

            serializer = AppLLMAgentListSerializer(clone)
            return get_api_response(
                True,
                {
                    "message": f"Agent duplicated as '{copy_name}'",
                    "agent": serializer.data,
                },
                200,
            )
        except AppLLMAgent.DoesNotExist:
            return get_api_response(False, {"message": "Agent not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentTestViewAPIV1(ZangoGenericPlatformAPIView):
    """
    POST /api/v1/apps/<app_uuid>/ai/agents/<agent_id>/test/
    Runs a minimal test invocation.
    """

    def post(self, request, app_uuid, agent_id, *args, **kwargs):
        try:
            agent = AppLLMAgent.objects.select_related(
                "provider",
                "system_prompt__active_version",
                "user_prompt__active_version",
            ).get(id=agent_id)
            print(agent)
            from django.db import connection

            print(connection.tenant)
            if not agent.provider:
                return get_api_response(
                    False, {"message": "Agent has no provider configured"}, 400
                )

            # Use AgentClient so agent metadata is captured in invocation logs
            from zango.ai.agent_client import AgentClient
            from zango.ai.providers.base import LLMMessage
            from zango.apps.dynamic_models.workspace.base import Workspace
            from zango.apps.shared.tenancy.models import TenantModel

            variables = request.data.get("variables", {})
            tenant = TenantModel.objects.get(uuid=app_uuid)
            connection.set_tenant(tenant)
            with connection.cursor() as c:
                ws = Workspace(connection.tenant, request=None, as_systemuser=True)
                ws.ready()

                agent_client = AgentClient(agent)

                messages = None
                if not agent.user_prompt:
                    messages = [
                        LLMMessage(
                            role="user",
                            content="generate assessment for Employee ID 2 based on past 30 days performance for topic Biology.",
                        )
                    ]

                response = agent_client.run(
                    variables=variables or None,
                    messages=messages,
                    triggered_by="system",
                )

                return get_api_response(
                    True,
                    {
                        "message": "Test successful",
                        "result": {
                            "content": response.content[:500],
                            "model": response.model,
                            "latency_ms": response.latency_ms,
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens,
                            "cost_usd": response.cost_usd,
                        },
                    },
                    200,
                )
        except AppLLMAgent.DoesNotExist:
            return get_api_response(False, {"message": "Agent not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


# ── Agent Memory Session Views ──────────────────────────────────────────────


@method_decorator(set_app_schema_path, name="dispatch")
class AgentSessionsListViewAPIV1(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    """
    GET /api/v1/apps/<app_uuid>/ai/agents/<agent_id>/sessions/
    List memory sessions for an agent.
    Supports ?search= (session_id or user_ref) and ?is_active=true|false.
    """

    pagination_class = ZangoAPIPagination

    def get(self, request, app_uuid, agent_id, *args, **kwargs):
        from zango.api.platform.ai.v1.serializers import AppLLMMemorySessionSerializer

        try:
            agent = AppLLMAgent.objects.get(id=agent_id)
            qs = agent.sessions.all()

            search = request.GET.get("search", "")
            if search:
                qs = qs.filter(
                    Q(session_id__icontains=search) | Q(user_ref__icontains=search)
                )

            is_active = request.GET.get("is_active")
            if is_active is not None:
                qs = qs.filter(is_active=is_active.lower() == "true")

            paginated = self.paginate_queryset(qs, request, view=self)
            serializer = AppLLMMemorySessionSerializer(paginated, many=True)
            paginated_data = self.get_paginated_response_data(serializer.data)

            return get_api_response(
                True,
                {
                    "sessions": paginated_data,
                    "message": "Sessions fetched successfully",
                },
                200,
            )
        except AppLLMAgent.DoesNotExist:
            return get_api_response(False, {"message": "Agent not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class AgentSessionDetailViewAPIV1(ZangoGenericPlatformAPIView):
    """
    GET    /api/v1/apps/<app_uuid>/ai/agents/<agent_id>/sessions/<session_id_str>/
    DELETE /api/v1/apps/<app_uuid>/ai/agents/<agent_id>/sessions/<session_id_str>/
    """

    def get(self, request, app_uuid, agent_id, session_id_str, *args, **kwargs):
        from zango.api.platform.ai.v1.serializers import (
            AppLLMMemorySessionDetailSerializer,
        )
        from zango.apps.ai.models.memory import AppLLMMemorySession

        try:
            agent = AppLLMAgent.objects.get(id=agent_id)
            session = AppLLMMemorySession.objects.get(
                agent=agent, session_id=session_id_str
            )
            serializer = AppLLMMemorySessionDetailSerializer(session)
            return get_api_response(
                True,
                {"session": serializer.data, "message": "Session fetched successfully"},
                200,
            )
        except AppLLMAgent.DoesNotExist:
            return get_api_response(False, {"message": "Agent not found"}, 404)
        except AppLLMMemorySession.DoesNotExist:
            return get_api_response(False, {"message": "Session not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)

    def delete(self, request, app_uuid, agent_id, session_id_str, *args, **kwargs):
        from zango.ai.agent_client import AgentClient

        try:
            agent = AppLLMAgent.objects.get(id=agent_id)
            client = AgentClient(agent)
            found = client.clear_session(session_id_str)
            if not found:
                return get_api_response(False, {"message": "Session not found"}, 404)
            return get_api_response(
                True, {"message": "Session cleared successfully"}, 200
            )
        except AppLLMAgent.DoesNotExist:
            return get_api_response(False, {"message": "Agent not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


# ── Tool Views ──────────────────────────────────────────────────────────────


@method_decorator(set_app_schema_path, name="dispatch")
class ToolsListViewAPIV1(ZangoGenericPlatformAPIView, ZangoAPIPagination):
    pagination_class = ZangoAPIPagination

    def get(self, request, app_uuid, *args, **kwargs):
        try:
            tools = AppLLMTool.objects.all()
            search = request.GET.get("search", "")
            if search:
                tools = tools.filter(
                    Q(name__icontains=search) | Q(description__icontains=search)
                )
            section = request.GET.get("section")
            if section:
                tools = tools.filter(section=section)
            safety = request.GET.get("safety")
            if safety:
                tools = tools.filter(safety=safety)
            is_active = request.GET.get("is_active")
            if is_active is not None:
                tools = tools.filter(is_active=is_active.lower() == "true")

            stats = {
                "active_tools": AppLLMTool.objects.filter(is_active=True).count(),
                "sections": AppLLMTool.objects.filter(is_active=True)
                .values("section")
                .distinct()
                .count(),
            }

            paginated = self.paginate_queryset(tools, request, view=self)
            serializer = AppLLMToolListSerializer(paginated, many=True)
            paginated_data = self.get_paginated_response_data(serializer.data)
            return get_api_response(
                True, {"tools": paginated_data, "stats": stats}, 200
            )
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class ToolDetailViewAPIV1(ZangoGenericPlatformAPIView):
    def get(self, request, app_uuid, tool_id, *args, **kwargs):
        try:
            tool = AppLLMTool.objects.get(id=tool_id)
            serializer = AppLLMToolDetailSerializer(tool)
            return get_api_response(True, {"tool": serializer.data}, 200)
        except AppLLMTool.DoesNotExist:
            return get_api_response(False, {"message": "Tool not found"}, 404)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class ToolSyncViewAPIV1(ZangoGenericPlatformAPIView):
    def post(self, request, app_uuid, *args, **kwargs):
        try:
            from zango.apps.dynamic_models.workspace.base import Workspace
            from zango.apps.shared.tenancy.models import TenantModel

            tenant = TenantModel.objects.get(uuid=app_uuid)
            connection.set_tenant(tenant)
            with connection.cursor() as c:
                ws = Workspace(connection.tenant, request=None, as_systemuser=True)
                ws.ready()
                stats = ws.sync_tools()

            return get_api_response(
                True, {"message": "Tool sync complete", "stats": stats}, 200
            )
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)


@method_decorator(set_app_schema_path, name="dispatch")
class ToolSectionsViewAPIV1(ZangoGenericPlatformAPIView):
    def get(self, request, app_uuid, *args, **kwargs):
        try:
            from django.db.models import Count

            sections = (
                AppLLMTool.objects.values("section")
                .annotate(
                    count=Count("id"),
                    active_count=Count("id", filter=Q(is_active=True)),
                )
                .order_by("section")
            )
            return get_api_response(True, {"sections": list(sections)}, 200)
        except Exception as e:
            return get_api_response(False, {"message": str(e)}, 500)
