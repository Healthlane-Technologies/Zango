"""Defines which authentication backend for app users."""

from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import AppUserModel


class AppUserModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None):
        if request and request.tenant.tenant_type == "app":
            try:
                user = AppUserModel.objects.get(Q(email=username) | Q(mobile=username))
                pwd_valid = user.check_password(password)
                if pwd_valid and user.is_active:
                    return user
                return None
            except AppUserModel.DoesNotExist:
                return None

    def get_user(self, user_id):
        """
        Method for getting user data by passing user_id
        """
        try:
            return AppUserModel.objects.get(pk=user_id)
        except AppUserModel.DoesNotExist:
            return None
