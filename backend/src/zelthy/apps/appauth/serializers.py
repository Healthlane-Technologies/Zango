from rest_framework import serializers
from .models import UserRoleModel, AppUserModel

class UserRoleSerializerModel(serializers.ModelSerializer):

    class Meta:
        model = UserRoleModel 
        fields = '__all__'


class AppUserSerializerModel(serializers.ModelSerializer):

    class Meta:
        model = AppUserModel
        fields = '__all__'