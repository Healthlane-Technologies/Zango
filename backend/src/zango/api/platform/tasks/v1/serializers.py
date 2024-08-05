import json
import inspect

from django_celery_beat.models import CrontabSchedule
from django.db import connection
from rest_framework import serializers
from django_celery_results.models import TaskResult
from django_celery_beat.models import PeriodicTask


from zango.api.platform.permissions.v1.serializers import PolicySerializer
from zango.apps.tasks.models import AppTask
from zango.apps.tasks.utils import get_crontab_obj
from zango.apps.dynamic_models.workspace.base import Workspace


class CronTabSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrontabSchedule
        fields = [
            "minute",
            "hour",
            "day_of_week",
            "day_of_month",
            "month_of_year",
        ]


class TaskSerializer(serializers.ModelSerializer):
    attached_policies = PolicySerializer(many=True)
    crontab = CronTabSerializer()
    schedule = serializers.SerializerMethodField()
    docstring = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField()
    run_history = serializers.SerializerMethodField()

    class Meta:
        model = AppTask
        fields = "__all__"

    def update(self, instance, validated_data):
        if self.context.get("cronexp"):
            cronexp = json.loads(self.context.get("cronexp"))
            try:
                schedule, success = get_crontab_obj(cronexp)
                crontab = schedule
                validated_data["crontab"] = crontab
            except ValueError:
                raise serializers.ValidationError("Invalid cron expression")
        return super(TaskSerializer, self).update(instance, validated_data)

    def get_schedule(self, obj):
        return str(obj.crontab)[:-18]

    def get_docstring(self, obj):
        try:
            md = self.context.get("plugin_source").load_plugin(
                obj.name[: obj.name.rfind(".")]
            )
            task = getattr(md, obj.name[obj.name.rfind(".") + 1 :])
            docstring = task.__doc__
            return docstring
        except Exception:
            return ""

    def get_code(self, obj):
        try:
            md = self.context.get("plugin_source").load_plugin(
                obj.name[: obj.name.rfind(".")]
            )
            task = getattr(md, obj.name[obj.name.rfind(".") + 1 :])
            code = inspect.getsource(task)
            return code
        except Exception:
            return ""

    def get_run_history(self, obj):
        if not self.context.get("history"):
            return []
        ptask = PeriodicTask.objects.get(id=obj.master_task_id)
        serializer = TaskResultSerializer(
            TaskResult.objects.filter(periodic_task_name=ptask.name).order_by(
                "-date_done"
            ),
            many=True,
        )
        return serializer.data


class TaskResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskResult
        fields = ["date_created", "date_done", "result", "traceback"]
