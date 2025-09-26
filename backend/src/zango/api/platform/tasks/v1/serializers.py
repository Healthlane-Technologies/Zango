import inspect
import json

from django_celery_beat.models import CrontabSchedule, PeriodicTask
from django_celery_results.models import TaskResult
from rest_framework import serializers

from zango.api.platform.permissions.v1.serializers import PolicySerializer
from zango.apps.tasks.models import AppTask
from zango.apps.tasks.utils import get_crontab_obj
from zango.core.utils import get_datetime_str_in_tenant_timezone


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
    crontab = serializers.SerializerMethodField()
    schedule = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField()
    run_history = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    modified_at = serializers.SerializerMethodField()

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

    def get_crontab(self, obj):
        try:
            if obj.crontab:
                return CronTabSerializer(obj.crontab).data
        except CrontabSchedule.DoesNotExist:
            pass
        return None

    def get_schedule(self, obj):
        try:
            if obj.crontab:
                return str(obj.crontab)[:-18]
        except CrontabSchedule.DoesNotExist:
            pass
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
        try:
            if obj.master_task_id:
                ptask = PeriodicTask.objects.get(id=obj.master_task_id)
                serializer = TaskResultSerializer(
                    TaskResult.objects.filter(periodic_task_name=ptask.name).order_by(
                        "-date_done"
                    ),
                    many=True,
                )
                return serializer.data
        except PeriodicTask.DoesNotExist:
            pass
        return []

    def get_created_at(self, obj):
        return get_datetime_str_in_tenant_timezone(
            obj.created_at, self.context.get("tenant")
        )

    def get_modified_at(self, obj):
        return get_datetime_str_in_tenant_timezone(
            obj.modified_at, self.context.get("tenant")
        )


class TaskResultSerializer(serializers.ModelSerializer):
    date_started = serializers.SerializerMethodField()
    date_done = serializers.SerializerMethodField()

    class Meta:
        model = TaskResult
        fields = [
            "date_started",
            "date_done",
            "result",
            "traceback",
            "status",
            "task_args",
            "task_kwargs",
            "worker",
        ]

    def get_date_started(self, obj):
        return obj.date_done.strftime("%Y-%m-%d %H:%M:%S")

    def get_date_done(self, obj):
        return obj.date_done.strftime("%Y-%m-%d %H:%M:%S")
