# -*- coding: utf-8 -*-
from datetime import datetime

from django.db import connection
from ipware import get_client_ip
from django.dispatch import receiver
from axes.helpers import get_client_user_agent
from django.contrib.auth.signals import (
    user_logged_out,
    user_login_failed,
    user_logged_in,
)

from .models import AppAccessLog
from zelthy.apps.appauth.models import UserRoleModel
from zelthy.core.utils import get_current_request


@receiver(user_login_failed)
def login_failure_handler(sender, **kwargs):
    if connection.schema_name != "public":
        creds = kwargs.get("credentials", {})
        request = kwargs.get("request", get_current_request())
        client_ip, is_routable = get_client_ip(request)
        access_log = AppAccessLog.objects.create(
            ip_address=client_ip,
            http_accept=request.META.get("HTTP_ACCEPT", "<unknown>"),
            path_info=request.META.get("PATH_INFO", "<unknown>"),
            user_agent=get_client_user_agent(request),
            username=creds.get("username"),
            attempt_time=datetime.now(),
            attempt_type="login",
            is_login_successful=False,
        )


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):

    if connection.schema_name != "public":
        try:
            client_ip, is_routable = get_client_ip(request)
            username = request.POST.get("auth-username") or request.data.get("username")
            user_role = None
            access_log = AppAccessLog.objects.create(
                ip_address=client_ip,
                http_accept=request.META.get("HTTP_ACCEPT", "<unknown>"),
                path_info=request.META.get("PATH_INFO", "<unknown>"),
                username=username,
                user_agent=get_client_user_agent(request),
                attempt_time=datetime.now(),
                attempt_type="login",
                is_login_successful=True,
                user=user,
            )

            if getattr(request, "selected_role_id", ""):
                user_role = UserRoleModel.objects.filter(
                    id=getattr(request, "selected_role_id")
                ).last()

            if user_role:
                access_log.role = user_role
                access_log.save()
        except:
            import traceback

            print(traceback.format_exc())


@receiver(user_logged_out)
def user_logged_out_handler(sender, user, **kwargs):
    if connection.schema_name != "public":
        access_log = AppAccessLog.objects.filter(
            user=user, session_expired_at__isnull=True
        ).last()

        if access_log:
            access_log.session_expired_at = datetime.now()
            access_log.save()
