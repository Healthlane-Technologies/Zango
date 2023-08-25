from rest_framework import serializers
from .models import ProgramModel


class ProgramModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramModel
        fields = '__all__'
    

    def validate_program_name(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Program name is to short.")
        return value