import json

from django_celery_beat.models import CrontabSchedule
from rest_framework import serializers

from zelthy.apps.tasks.models import AppTask
from zelthy.api.platform.permissions.v1.serializers import PolicySerializer
from zelthy.apps.tasks.utils import get_crontab_obj


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
