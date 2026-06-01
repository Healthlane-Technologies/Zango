"""Models for the Platform Logs feature.

Configuration only — the actual log lines live in CloudWatch (or whichever
backend a given connector is wired to). This module owns the mapping from
(environment × component) → connector + config.

Lives in the public/shared schema: one row applies to every tenant.
"""

from __future__ import annotations

import uuid

from django.db import models

from zango.core.model_mixins import FullAuditMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Component(models.TextChoices):
    APP = "app", "App"
    CELERY = "celery", "Celery worker"
    CELERY_BEAT = "celery_beat", "Celery beat"


class ConnectorType(models.TextChoices):
    CLOUDWATCH = "cloudwatch", "AWS CloudWatch Logs"
    # Future:
    # DYNAMODB   = "dynamodb",      "AWS DynamoDB"
    # OTEL_HTTP  = "otel_http",     "OpenTelemetry OTLP/HTTP"
    # ELASTIC    = "elasticsearch", "Elasticsearch"


# ---------------------------------------------------------------------------
# LogConnectorConfig — one row per (environment × component)
# ---------------------------------------------------------------------------


class LogConnectorConfig(FullAuditMixin):
    """Pairs a (env, component) with a connector type and its config blob.

    The `config` JSON is connector-specific. For CloudWatch:
        {
            "region": "ap-south-1",
            "log_group_name": "/ecs/zango-india-staging/app",
            "stream_prefix": null,
            "format": "verbose",     // "plain" | "verbose" | "json"
            "role_arn": null
        }

    Identity:
    - `id` is Django's default auto-increment BigAutoField (for relational
      integrity and cheap FK joins — not added here, Django provides it).
    - `object_uuid` is the stable, externally-visible identifier used in
      URLs and API responses.
    """

    object_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        editable=False,
    )

    environment = models.CharField(
        max_length=32,
        help_text="Mirrors settings.ENV — e.g. 'local', 'staging', 'prod'.",
    )
    component = models.CharField(max_length=16, choices=Component.choices)
    connector = models.CharField(max_length=32, choices=ConnectorType.choices)
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "platform_log_connector_config"
        ordering = ["environment", "component"]
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "component"],
                name="platform_logs_unique_env_component",
            ),
        ]
        indexes = [
            models.Index(fields=["environment", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.environment}:{self.component} → {self.connector}"
