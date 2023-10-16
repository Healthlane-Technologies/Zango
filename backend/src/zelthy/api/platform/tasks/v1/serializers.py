import json

from rest_framework import serializers
from zelthy.apps.tasks.models import AppTask


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppTask
        fields = "__all__"
