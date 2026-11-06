from django.db import models
from zango.apps.dynamic_models.models import DynamicModelBase


class ZasSequence(DynamicModelBase):
    """One counter per auto-sequence field (key = "<entity>.<field>[.<period>]")."""

    key = models.CharField(max_length=200, unique=True)
    value = models.BigIntegerField(default=0)

    def __str__(self):
        return f"{self.key}={self.value}"


class ZasAiRun(DynamicModelBase):
    """One run of an AI helper (spec ai.agents): queued → running → done | failed | unavailable.
    created_by is the person who started it (none for background triggers)."""

    agent = models.CharField(max_length=100, db_index=True)
    entity = models.CharField(max_length=100, blank=True, default="")
    record_uuid = models.CharField(max_length=64, blank=True, default="", db_index=True)
    trigger = models.CharField(max_length=30)
    role = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(max_length=20, default="queued", db_index=True)
    inputs = models.JSONField(default=dict, blank=True)
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(blank=True, default="")
    applied = models.BooleanField(default=False)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.agent} {self.trigger} {self.status}"


class ZasAiSuggestion(DynamicModelBase):
    """Values an AI helper proposes for a record (review: suggest), waiting for a person."""

    run = models.ForeignKey(ZasAiRun, on_delete=models.CASCADE, related_name="suggestions")
    agent = models.CharField(max_length=100, db_index=True)
    entity = models.CharField(max_length=100)
    record_uuid = models.CharField(max_length=64, db_index=True)
    values = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default="pending", db_index=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.agent} → {self.entity} {self.status}"
