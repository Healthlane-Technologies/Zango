from rest_framework import serializers
from .models import CompanyAccount


class CompanyAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAccount
        fields = '__all__'
    

    def validate_full_name(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Full name is to short.")
        return value