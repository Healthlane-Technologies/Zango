import json

from django.db import models
from django_celery_beat.models import CrontabSchedule, IntervalSchedule
from django_celery_beat.models import PeriodicTask

from zelthy.core.model_mixins import FullAuditMixin
from zelthy.apps.permissions.models import PolicyModel


class AppTask(FullAuditMixin):
    name = models.CharField(max_length=255, unique=True)
    is_enabled = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    task = "zelthy.core.tasks.zelthy_task_executor"
    interval = models.ForeignKey(
        IntervalSchedule,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="interval",
    )
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
    master_task = models.ForeignKey(
        PeriodicTask, null=True, blank=True, on_delete=models.CASCADE
    )
    attached_policies = models.ManyToManyField(PolicyModel, blank=True, null=True)

    def schedule(self):
        return self.master_task.schedule

    def save(self, *args, **kwargs):
        # validating imports of code
        # not_allowed_imports = validate_imports(self.code)
        # if not_allowed_imports:
        #     raise ValidationError("Code contains imports which are not allowed to use.")

        import uuid

        if not self.master_task:
            obj = PeriodicTask(
                name=uuid.uuid4(),
                task=self.task,
                interval=self.interval,
                crontab=self.crontab,
                # solar=self.solar,
                args=self.args,
                kwargs=self.kwargs,
                # expires=self.expires,
                enabled=self.is_enabled,
                # date_changed=self.date_changed,
                # description=self.description,
            )
            obj.save()

            self.master_task = obj
        else:
            obj = self.master_task
            obj.task = self.task
            obj.interval = self.interval
            obj.crontab = self.crontab
            # obj.solar = self.solar
            obj.args = self.args
            obj.kwargs = json.dumps(self.kwargs)
            # obj.expires = self.expires
            obj.enabled = self.is_enabled
            # obj.date_changed = self.date_changed
            # obj.description = self.description
            obj.save()

        super(AppTask, self).save(*args, **kwargs)
