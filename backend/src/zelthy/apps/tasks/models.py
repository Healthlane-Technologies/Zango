from django.db import models
from django_celery_beat.models import CrontabSchedule

from zelthy.core.model_mixins import FullAuditMixin


class AppTask(FullAuditMixin):
    name = models.CharField(max_length=255, unique=True)
    module_path = models.TextField(unique=True)
    is_enabled = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    crontab = models.ForeignKey(
        CrontabSchedule,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="crontab",
        help_text="Crontab Schedule",
    )
    args = models.JSONField(null=True, blank=True)
    kwargs = models.JSONField(null=True, blank=True)
