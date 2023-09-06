from rest_framework import serializers
from .models import Patient, PatientProgramModel


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class PatientProgramModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProgramModel
        fields = '__all__'