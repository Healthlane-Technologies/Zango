from rest_framework.serializers import ModelSerializer
from .models import SystemDetails


class SystemDetailsSerializers(ModelSerializer):
    class Meta:
        model = SystemDetails
        fields = '__all__'