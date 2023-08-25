from rest_framework import serializers
from .models import BenefitsModel


class BenefitsModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenefitsModel
        fields = '__all__'
    

    # def validate_program_name(self, value):
    #     if len(value) < 5:
    #         raise serializers.ValidationError("Program name is to short.")
    #     return value