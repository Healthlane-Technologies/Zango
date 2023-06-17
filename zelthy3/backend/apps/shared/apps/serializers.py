from rest_framework import serializers
from .models import AppModel

class AppSerializerModel(serializers.ModelSerializer):
    
    class Meta:
        model = AppModel 
        fields = '__all__'


