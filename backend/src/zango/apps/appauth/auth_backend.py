"""Defines which authentication backend for app users."""

import binascii

from hmac import compare_digest

from knox.auth import TokenAuthentication
from knox.crypto import hash_token
from knox.settings import CONSTANTS, knox_settings
from rest_framework import exceptions
from rest_framework.authentication import (
    get_authorization_header,
)

from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .models import AppUserAuthToken, AppUserModel


class AppUserModelBackend(ModelBackend):
    def authenticate(
        self, request, username=None, password=None, email=None, phone=None
    ):
        if request and request.tenant.tenant_type == "app":
            try:
                query = Q()
                if email:
                    query = query | Q(email=email)
                if phone:
                    query = query | Q(mobile=phone)
                if username:
                    query = query | Q(email=username) | Q(mobile=username)
                user = AppUserModel.objects.get(query)
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


class KnoxTokenAuthBackend(TokenAuthentication):
    def authenticate(self, request):
        if request is None or getattr(request, "internal_routing", False):
            return None
        elif request and request.tenant.tenant_type == "app":
            resp = self.authenticate_app_creds(request)
            if resp:
                user, token = resp
                request.user = user
                request.auth = token
                return (user, token)
            return resp
        else:
            return super().authenticate(request)

    def authenticate_app_creds(self, request):
        auth = get_authorization_header(request).split()
        prefix = self.authenticate_header(request).encode()

        if not auth:
            return None
        if auth[0].lower() != prefix.lower():
            # Authorization header is possibly for another backend
            return None
        if len(auth) == 1:
            msg = _("Invalid token header. No credentials provided.")
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _("Invalid token header. " "Token string should not contain spaces.")
            raise exceptions.AuthenticationFailed(msg)

        msg = _("Invalid token.")
        token = auth[1].decode("utf-8")

        for auth_token in AppUserAuthToken.objects.filter(
            token_key=token[: CONSTANTS.TOKEN_KEY_LENGTH]
        ):
            if self._cleanup_token(auth_token):
                continue

            try:
                digest = hash_token(token)
            except (TypeError, binascii.Error):
                raise exceptions.AuthenticationFailed(msg)
            if compare_digest(digest, auth_token.digest):
                if knox_settings.AUTO_REFRESH and auth_token.expiry:
                    self.renew_token(auth_token)
                return self.validate_user(auth_token)
        raise exceptions.AuthenticationFailed(msg)
