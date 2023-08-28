from rest_framework import serializers
from .models import BenefitsModel, DispensingOptionsModel


class BenefitsModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = BenefitsModel
        fields = '__all__'
    

    # def validate_program_name(self, value):
    #     if len(value) < 5:
    #         raise serializers.ValidationError("Program name is to short.")
    #     return value


class DispensingOptionsModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispensingOptionsModel
        fields = '__all__'