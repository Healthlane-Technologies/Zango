from decimal import Decimal

from rest_framework import serializers

from django.db import models

from zango.ai.encryption import encrypt_config, mask_config
from zango.ai.providers.registry import PROVIDER_REGISTRY
from zango.apps.ai.models import (
    AppLLMAgent,
    AppLLMInvocation,
    AppLLMPrompt,
    AppLLMPromptVersion,
    AppLLMProvider,
    AppLLMProviderModel,
    AppLLMTool,
    AppLLMToolCall,
)
from zango.apps.ai.models.memory import AppLLMMemoryMessage, AppLLMMemorySession


class AppLLMProviderModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppLLMProviderModel
        fields = [
            "id",
            "model_id",
            "display_name",
            "input_cost_per_mtok_override",
            "output_cost_per_mtok_override",
            "is_enabled",
            "rate_limit_rpm",
        ]


class AppLLMProviderListSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    models_count = serializers.SerializerMethodField()
    masked_config = serializers.SerializerMethodField()
    budget_status = serializers.SerializerMethodField()
    enabled_models = AppLLMProviderModelSerializer(many=True, read_only=True)

    class Meta:
        model = AppLLMProvider
        fields = [
            "id",
            "name",
            "description",
            "provider_slug",
            "default_model",
            "is_enabled",
            "is_validated",
            "last_validated_at",
            "validation_error",
            "rate_limit_rpm",
            "rate_limit_tpm",
            "monthly_budget_usd",
            "budget_alert_threshold",
            "current_month_spend_usd",
            "total_invocations",
            "total_input_tokens",
            "total_output_tokens",
            "total_cost_usd",
            "created_at",
            "modified_at",
            "status",
            "models_count",
            "masked_config",
            "budget_status",
            "enabled_models",
        ]

    def get_status(self, obj):
        return "active" if obj.is_enabled else "inactive"

    def get_models_count(self, obj):
        return obj.enabled_models.count()

    def get_masked_config(self, obj):
        """Return config with secrets masked."""
        try:
            config = obj._decrypt_config()
            provider_cls = PROVIDER_REGISTRY.get(obj.provider_slug)
            if provider_cls:
                secret_fields = [
                    f["name"]
                    for f in getattr(provider_cls, "config_fields", [])
                    if f.get("type") == "secret"
                ]
                return mask_config(config, secret_fields)
            return mask_config(config, ["api_key"])
        except Exception:
            return {}

    def get_budget_status(self, obj):
        return obj.check_budget()


class AppLLMProviderCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    provider_slug = serializers.CharField(max_length=50)
    config = serializers.DictField()
    default_model = serializers.CharField(max_length=100)
    # Optional: list of model dicts fetched from the live API by the wizard.
    # If provided, these are stored as AppLLMProviderModel records instead of
    # the provider class's static supported_models list.
    fetched_models = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )
    rate_limit_rpm = serializers.IntegerField(
        required=False, allow_null=True, default=None
    )
    rate_limit_tpm = serializers.IntegerField(
        required=False, allow_null=True, default=None
    )
    monthly_budget_usd = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True, default=None
    )
    budget_alert_threshold = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, default=Decimal("80.00")
    )

    def validate_provider_slug(self, value):
        if value not in PROVIDER_REGISTRY:
            raise serializers.ValidationError(
                f"Provider '{value}' is not available. "
                f"Available: {list(PROVIDER_REGISTRY.keys())}"
            )
        return value

    def validate(self, data):
        """Validate required config fields per provider's config_fields spec,
        then validate the API key and fetch available models from the provider."""
        slug = data.get("provider_slug")
        config = data.get("config", {})
        provider_cls = PROVIDER_REGISTRY.get(slug)

        if provider_cls:
            for field_def in getattr(provider_cls, "config_fields", []):
                # Skip fields that are handled as top-level model fields
                if field_def.get("options_from") == "supported_models":
                    continue
                if field_def.get("required") and not config.get(field_def["name"]):
                    raise serializers.ValidationError(
                        {
                            "config": f"Missing required config field: {field_def['name']}"
                        }
                    )

            # Build a full config dict including default_model for providers that need it
            full_config = dict(config)
            full_config.setdefault("default_model", data.get("default_model", ""))

            # Validate API key / credentials before saving
            try:
                client = provider_cls(full_config)
                is_valid, error_msg = client.validate_config()
            except Exception as exc:
                raise serializers.ValidationError(
                    {"config": f"Provider initialisation failed: {exc}"}
                )

            if not is_valid:
                raise serializers.ValidationError(
                    {"config": f"API key validation failed: {error_msg}"}
                )

            # Use fetched_models from the wizard if provided; otherwise fall back
            # to the provider's static supported_models list.
            fetched_models = data.get("fetched_models") or []
            if fetched_models:
                data["_resolved_models"] = fetched_models
            else:
                try:
                    data["_resolved_models"] = client.get_models()
                except Exception:
                    data["_resolved_models"] = getattr(
                        provider_cls, "supported_models", []
                    )

        return data

    def create(self, validated_data):
        # Pop internal keys not part of the model fields
        resolved_models = validated_data.pop("_resolved_models", None)
        validated_data.pop("fetched_models", None)

        config = validated_data.pop("config")
        encrypted = encrypt_config(config)

        provider = AppLLMProvider.objects.create(
            name=validated_data["name"],
            description=validated_data.get("description", ""),
            provider_slug=validated_data["provider_slug"],
            config_encrypted=encrypted,
            default_model=validated_data["default_model"],
            rate_limit_rpm=validated_data.get("rate_limit_rpm"),
            rate_limit_tpm=validated_data.get("rate_limit_tpm"),
            monthly_budget_usd=validated_data.get("monthly_budget_usd"),
            budget_alert_threshold=validated_data.get(
                "budget_alert_threshold", Decimal("80.00")
            ),
            # Mark as validated since we just confirmed the credentials work
            is_validated=True,
        )

        # Use dynamically fetched models if available, otherwise fall back to
        # the static supported_models list on the provider class
        provider_cls = PROVIDER_REGISTRY.get(validated_data["provider_slug"])
        models_to_create = resolved_models
        if not models_to_create and provider_cls:
            models_to_create = getattr(provider_cls, "supported_models", [])

        for model_info in models_to_create or []:
            AppLLMProviderModel.objects.create(
                provider=provider,
                model_id=model_info["id"],
                display_name=model_info["name"],
                is_enabled=True,
            )

        return provider


class AppLLMProviderUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    config = serializers.DictField(required=False)
    default_model = serializers.CharField(max_length=100, required=False)
    rate_limit_rpm = serializers.IntegerField(required=False, allow_null=True)
    rate_limit_tpm = serializers.IntegerField(required=False, allow_null=True)
    monthly_budget_usd = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    budget_alert_threshold = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False
    )

    def update(self, instance, validated_data):
        config = validated_data.pop("config", None)

        if config is not None:
            # If config contains masked secret values, preserve existing values
            try:
                existing_config = instance._decrypt_config()
            except Exception:
                existing_config = {}

            provider_cls = PROVIDER_REGISTRY.get(instance.provider_slug)
            secret_fields = []
            if provider_cls:
                secret_fields = [
                    f["name"]
                    for f in getattr(provider_cls, "config_fields", [])
                    if f.get("type") == "secret"
                ]

            for field_name in secret_fields:
                new_val = config.get(field_name, "")
                if new_val and "****" in str(new_val):
                    # Masked value — keep existing
                    config[field_name] = existing_config.get(field_name, "")

            instance.config_encrypted = encrypt_config(config)

        for attr in [
            "name",
            "description",
            "default_model",
            "rate_limit_rpm",
            "rate_limit_tpm",
            "monthly_budget_usd",
            "budget_alert_threshold",
        ]:
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])

        instance.save()
        return instance


class AppLLMInvocationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppLLMInvocation
        fields = [
            "id",
            "run_id",
            "session_id",
            "round_number",
            "provider_name",
            "provider_slug",
            "model",
            "agent_name",
            "input_tokens",
            "output_tokens",
            "cost_usd",
            "latency_ms",
            "triggered_by",
            "status",
            "error_type",
            "stop_reason",
            "created_at",
        ]


class AppLLMInvocationDetailSerializer(serializers.ModelSerializer):
    prompt_info = serializers.SerializerMethodField()
    cost_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = AppLLMInvocation
        fields = [
            "id",
            "run_id",
            "session_id",
            "round_number",
            "provider",
            "provider_name",
            "provider_slug",
            "model",
            "agent",
            "agent_name",
            "request_messages",
            "request_system",
            "request_tools",
            "request_params",
            "request_files",
            "response_content",
            "response_tool_calls",
            "stop_reason",
            "input_tokens",
            "output_tokens",
            "cache_creation_tokens",
            "cache_read_tokens",
            "cost_usd",
            "latency_ms",
            "time_to_first_token_ms",
            "triggered_by",
            "user_id_ref",
            "celery_task_id",
            "status",
            "error_message",
            "error_type",
            "system_prompt_name",
            "system_prompt_version",
            "user_prompt_name",
            "user_prompt_version",
            "rendered_system_prompt",
            "context_snapshot",
            "created_at",
            "modified_at",
            "prompt_info",
            "cost_breakdown",
        ]

    def get_prompt_info(self, obj):
        return {
            "system_prompt_name": obj.system_prompt_name or None,
            "system_prompt_version": obj.system_prompt_version,
            "user_prompt_name": obj.user_prompt_name or None,
            "user_prompt_version": obj.user_prompt_version,
            "rendered_system_prompt": obj.rendered_system_prompt,
        }

    def get_cost_breakdown(self, obj):
        return {
            "input_tokens": obj.input_tokens,
            "output_tokens": obj.output_tokens,
            "cache_creation_tokens": obj.cache_creation_tokens,
            "cache_read_tokens": obj.cache_read_tokens,
            "cost_usd": str(obj.cost_usd),
            "stop_reason": obj.stop_reason,
            "latency_ms": obj.latency_ms,
        }


# ── Prompt Serializers ──────────────────────────────────────────────────────


class AppLLMPromptVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppLLMPromptVersion
        fields = [
            "id",
            "version_number",
            "content",
            "change_description",
            "status",
            "variables",
            "created_at",
            "created_by",
            "modified_at",
        ]


class AppLLMPromptListSerializer(serializers.ModelSerializer):
    active_version_number = serializers.SerializerMethodField()
    total_versions = serializers.SerializerMethodField()
    active_version = AppLLMPromptVersionSerializer(read_only=True)
    versions = serializers.SerializerMethodField()
    used_by_agents = serializers.SerializerMethodField()

    class Meta:
        model = AppLLMPrompt
        fields = [
            "id",
            "name",
            "description",
            "type",
            "is_active",
            "active_version",
            "active_version_number",
            "versions",
            "total_versions",
            "used_by_agents",
            "created_at",
            "modified_at",
        ]

    def get_active_version_number(self, obj):
        if obj.active_version_id:
            return obj.active_version.version_number
        return None

    def get_total_versions(self, obj):
        return obj.versions.count()

    def get_versions(self, obj):
        versions = obj.versions.all().order_by("-version_number")
        return AppLLMPromptVersionSerializer(versions, many=True).data

    def get_used_by_agents(self, obj):
        agents = (
            AppLLMAgent.objects.filter(is_enabled=True)
            .filter(models.Q(system_prompt=obj) | models.Q(user_prompt=obj))
            .values("id", "name")
        )
        return list(agents)


class AppLLMPromptDetailSerializer(serializers.ModelSerializer):
    active_version = AppLLMPromptVersionSerializer(read_only=True)
    versions = serializers.SerializerMethodField()
    total_versions = serializers.SerializerMethodField()

    class Meta:
        model = AppLLMPrompt
        fields = [
            "id",
            "name",
            "description",
            "type",
            "is_active",
            "active_version",
            "versions",
            "total_versions",
            "created_at",
            "modified_at",
        ]

    def get_versions(self, obj):
        versions = obj.versions.all().order_by("-version_number")
        return AppLLMPromptVersionSerializer(versions, many=True).data

    def get_total_versions(self, obj):
        return obj.versions.count()


class AppLLMPromptCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    type = serializers.ChoiceField(choices=["system", "user"])
    content = serializers.CharField()
    change_description = serializers.CharField(
        required=False, default="Initial version", allow_blank=True
    )

    def validate_name(self, value):
        if AppLLMPrompt.objects.filter(name=value).exists():
            raise serializers.ValidationError(
                f"A prompt with name '{value}' already exists."
            )
        return value

    def create(self, validated_data):
        content = validated_data.pop("content")
        change_description = validated_data.pop("change_description", "Initial version")
        variables = AppLLMPromptVersion.extract_variables(content)

        prompt = AppLLMPrompt.objects.create(
            name=validated_data["name"],
            description=validated_data.get("description", ""),
            type=validated_data["type"],
        )

        version = AppLLMPromptVersion.objects.create(
            prompt=prompt,
            version_number=1,
            content=content,
            change_description=change_description,
            status="active",
            variables=variables,
        )

        prompt.active_version = version
        prompt.save()

        return prompt


class AppLLMPromptUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    type = serializers.ChoiceField(choices=["system", "user"], required=False)
    is_active = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        for attr in ["name", "description", "type", "is_active"]:
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])
        instance.save()
        return instance


class AppLLMPromptVersionCreateSerializer(serializers.Serializer):
    content = serializers.CharField()
    change_description = serializers.CharField(
        required=False, default="", allow_blank=True
    )

    def create(self, validated_data):
        prompt = self.context["prompt"]
        content = validated_data["content"]
        variables = AppLLMPromptVersion.extract_variables(content)

        from django.db.models import Max

        max_version = (
            prompt.versions.aggregate(Max("version_number"))["version_number__max"] or 0
        )

        version = AppLLMPromptVersion.objects.create(
            prompt=prompt,
            version_number=max_version + 1,
            content=content,
            change_description=validated_data.get("change_description", ""),
            status="draft",
            variables=variables,
        )

        return version


# ── Agent Serializers ───────────────────────────────────────────────────────


class AppLLMAgentListSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    provider_slug = serializers.SerializerMethodField()
    system_prompt_name = serializers.SerializerMethodField()
    user_prompt_name = serializers.SerializerMethodField()
    metrics = serializers.SerializerMethodField()
    session_count = serializers.SerializerMethodField()

    class Meta:
        model = AppLLMAgent
        fields = [
            "id",
            "name",
            "description",
            "provider",
            "provider_name",
            "provider_slug",
            "model",
            "system_prompt",
            "system_prompt_name",
            "user_prompt",
            "user_prompt_name",
            "temperature",
            "max_tokens",
            "timeout_seconds",
            "output_schema",
            "output_json_schema",
            "guardrails",
            "tools",
            "is_enabled",
            "status",
            "total_invocations",
            "total_cost_usd",
            "memory_enabled",
            "memory_max_messages",
            "session_count",
            "created_at",
            "modified_at",
            "metrics",
        ]

    def get_status(self, obj):
        return "active" if obj.is_enabled else "disabled"

    def get_provider_name(self, obj):
        return obj.provider.name if obj.provider else None

    def get_provider_slug(self, obj):
        return obj.provider.provider_slug if obj.provider else None

    def get_system_prompt_name(self, obj):
        return obj.system_prompt.name if obj.system_prompt else None

    def get_user_prompt_name(self, obj):
        return obj.user_prompt.name if obj.user_prompt else None

    def get_session_count(self, obj):
        if not obj.memory_enabled:
            return 0
        return obj.sessions.filter(is_active=True).count()

    def get_metrics(self, obj):
        """Compute metrics from AppLLMInvocation. Lightweight aggregation."""
        from datetime import timedelta

        from django.db.models import Avg, Count, Sum
        from django.utils import timezone

        # Base queryset — all invocations for this specific agent
        base_qs = AppLLMInvocation.objects.filter(agent=obj)

        totals = base_qs.aggregate(
            total_invocations=Count("id"),
            success_count=Count("id", filter=models.Q(status="success")),
            total_cost=Sum("cost_usd"),
            avg_latency=Avg("latency_ms"),
            avg_input_tokens=Avg("input_tokens"),
            avg_output_tokens=Avg("output_tokens"),
        )

        total = totals["total_invocations"] or 0
        success = totals["success_count"] or 0
        success_rate = round((success / total) * 100, 1) if total > 0 else 0

        # 24h count
        cutoff_24h = timezone.now() - timedelta(hours=24)
        invocations_24h = base_qs.filter(created_at__gte=cutoff_24h).count()

        avg_cost = 0
        if total > 0 and totals["total_cost"]:
            avg_cost = round(float(totals["total_cost"]) / total, 4)

        return {
            "totalInvocations": total,
            "successRate": success_rate,
            "avgLatency": f"{round((totals['avg_latency'] or 0) / 1000, 1)}s",
            "totalCost": float(totals["total_cost"] or 0),
            "avgInputTokens": round(totals["avg_input_tokens"] or 0),
            "avgOutputTokens": round(totals["avg_output_tokens"] or 0),
            "invocations24h": invocations_24h,
            "avgCost": avg_cost,
        }


class AppLLMAgentCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, default="", allow_blank=True)
    provider_id = serializers.IntegerField()
    model = serializers.CharField(max_length=100)
    system_prompt_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=""
    )
    user_prompt_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, default=""
    )
    temperature = serializers.FloatField(required=False, default=0.7)
    max_tokens = serializers.IntegerField(required=False, default=4096)
    timeout_seconds = serializers.IntegerField(required=False, default=30)
    output_schema = serializers.ChoiceField(
        choices=["JSON", "Text", "Markdown"], required=False, default="Text"
    )
    output_json_schema = serializers.JSONField(required=False, default=None)
    guardrails = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    tools = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    memory_enabled = serializers.BooleanField(required=False, default=False)
    memory_max_messages = serializers.IntegerField(
        required=False, default=20, min_value=1, max_value=200
    )

    def validate_output_json_schema(self, value):
        if value is not None and isinstance(value, dict):
            if "type" not in value:
                raise serializers.ValidationError(
                    "JSON Schema must have a 'type' field."
                )
        return value

    def validate_name(self, value):
        import re

        if not re.match(r"^[a-z0-9-]+$", value):
            raise serializers.ValidationError(
                "Name must contain only lowercase letters, numbers, and hyphens."
            )
        if AppLLMAgent.objects.filter(name=value).exists():
            raise serializers.ValidationError(
                f"An agent with name '{value}' already exists."
            )
        return value

    def validate(self, data):
        # Verify provider exists and is enabled
        try:
            provider = AppLLMProvider.objects.get(id=data["provider_id"])
            if not provider.is_enabled:
                raise serializers.ValidationError(
                    {"provider_id": "This provider is disabled."}
                )
        except AppLLMProvider.DoesNotExist:
            raise serializers.ValidationError({"provider_id": "Provider not found."})

        # Verify prompts exist if provided
        if data.get("system_prompt_name"):
            if not AppLLMPrompt.objects.filter(
                name=data["system_prompt_name"], is_active=True
            ).exists():
                raise serializers.ValidationError(
                    {
                        "system_prompt_name": f"Prompt '{data['system_prompt_name']}' not found."
                    }
                )
        if data.get("user_prompt_name"):
            if not AppLLMPrompt.objects.filter(
                name=data["user_prompt_name"], is_active=True
            ).exists():
                raise serializers.ValidationError(
                    {
                        "user_prompt_name": f"Prompt '{data['user_prompt_name']}' not found."
                    }
                )

        return data

    def create(self, validated_data):
        provider = AppLLMProvider.objects.get(id=validated_data.pop("provider_id"))

        system_prompt = None
        system_name = validated_data.pop("system_prompt_name", "")
        if system_name:
            system_prompt = AppLLMPrompt.objects.get(name=system_name, is_active=True)

        user_prompt = None
        user_name = validated_data.pop("user_prompt_name", "")
        if user_name:
            user_prompt = AppLLMPrompt.objects.get(name=user_name, is_active=True)

        agent = AppLLMAgent.objects.create(
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            **validated_data,
        )
        return agent


class AppLLMAgentUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    provider_id = serializers.IntegerField(required=False)
    model = serializers.CharField(max_length=100, required=False)
    system_prompt_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, allow_null=True
    )
    user_prompt_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, allow_null=True
    )
    temperature = serializers.FloatField(required=False)
    max_tokens = serializers.IntegerField(required=False)
    timeout_seconds = serializers.IntegerField(required=False)
    output_schema = serializers.ChoiceField(
        choices=["JSON", "Text", "Markdown"], required=False
    )
    output_json_schema = serializers.JSONField(required=False, allow_null=True)
    guardrails = serializers.ListField(child=serializers.CharField(), required=False)
    tools = serializers.ListField(child=serializers.CharField(), required=False)
    memory_enabled = serializers.BooleanField(required=False)
    memory_max_messages = serializers.IntegerField(
        required=False, min_value=1, max_value=200
    )

    def validate_output_json_schema(self, value):
        if value is not None and isinstance(value, dict):
            if "type" not in value:
                raise serializers.ValidationError(
                    "JSON Schema must have a 'type' field."
                )
        return value

    def update(self, instance, validated_data):
        # Handle provider FK
        if "provider_id" in validated_data:
            instance.provider = AppLLMProvider.objects.get(
                id=validated_data.pop("provider_id")
            )

        # Handle prompt FKs
        if "system_prompt_name" in validated_data:
            name = validated_data.pop("system_prompt_name")
            if name:
                instance.system_prompt = AppLLMPrompt.objects.get(
                    name=name, is_active=True
                )
            else:
                instance.system_prompt = None

        if "user_prompt_name" in validated_data:
            name = validated_data.pop("user_prompt_name")
            if name:
                instance.user_prompt = AppLLMPrompt.objects.get(
                    name=name, is_active=True
                )
            else:
                instance.user_prompt = None

        # Simple fields
        for attr in [
            "name",
            "description",
            "model",
            "temperature",
            "max_tokens",
            "timeout_seconds",
            "output_schema",
            "output_json_schema",
            "guardrails",
            "tools",
            "memory_enabled",
            "memory_max_messages",
        ]:
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])

        instance.save()
        return instance


# ── Tool Serializers ────────────────────────────────────────────────────────


class AppLLMToolListSerializer(serializers.ModelSerializer):
    params_count = serializers.SerializerMethodField()

    class Meta:
        model = AppLLMTool
        fields = [
            "id",
            "name",
            "description",
            "section",
            "safety",
            "timeout_seconds",
            "rate_limit_rpm",
            "return_type",
            "is_active",
            "total_calls",
            "total_errors",
            "total_timeouts",
            "avg_execution_ms",
            "last_called_at",
            "schema_hash",
            "python_path",
            "params_count",
        ]

    def get_params_count(self, obj):
        return len(obj.parameters_schema.get("properties", {}))


class AppLLMToolDetailSerializer(serializers.ModelSerializer):
    parameters_display = serializers.SerializerMethodField()

    class Meta:
        model = AppLLMTool
        fields = [
            "id",
            "name",
            "description",
            "section",
            "safety",
            "timeout_seconds",
            "rate_limit_rpm",
            "parameters_schema",
            "parameters_display",
            "python_path",
            "return_type",
            "is_active",
            "schema_hash",
            "total_calls",
            "total_errors",
            "total_timeouts",
            "avg_execution_ms",
            "last_called_at",
            "created_at",
            "modified_at",
        ]

    def get_parameters_display(self, obj):
        schema = obj.parameters_schema
        properties = schema.get("properties", {})
        required_set = set(schema.get("required", []))
        return [
            {
                "name": name,
                "type": prop.get("type", "string"),
                "required": name in required_set,
                "description": prop.get("description", ""),
                "enum": prop.get("enum"),
            }
            for name, prop in properties.items()
        ]


class AppLLMToolCallListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppLLMToolCall
        fields = [
            "id",
            "tool_name",
            "round_number",
            "tool_input",
            "tool_output",
            "status",
            "error_message",
            "execution_time_ms",
            "created_at",
        ]


# ── Memory Serializers ──────────────────────────────────────────────────────


class AppLLMMemoryMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppLLMMemoryMessage
        fields = [
            "id",
            "role",
            "content",
            "tool_calls",
            "tool_call_id",
            "sequence",
            "invocation",
            "created_at",
        ]


class AppLLMMemorySessionSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = AppLLMMemorySession
        fields = [
            "id",
            "session_id",
            "user_ref",
            "is_active",
            "last_active_at",
            "metadata",
            "message_count",
            "created_at",
            "modified_at",
        ]

    def get_message_count(self, obj):
        return obj.messages.count()


class AppLLMMemorySessionDetailSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = AppLLMMemorySession
        fields = [
            "id",
            "session_id",
            "user_ref",
            "is_active",
            "last_active_at",
            "metadata",
            "message_count",
            "messages",
            "created_at",
            "modified_at",
        ]

    def get_messages(self, obj):
        msgs = obj.messages.order_by("sequence").select_related("invocation")
        return AppLLMMemoryMessageSerializer(msgs, many=True).data

    def get_message_count(self, obj):
        return obj.messages.count()
