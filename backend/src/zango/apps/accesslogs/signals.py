from datetime import datetime

from axes.helpers import get_client_user_agent
from ipware import get_client_ip

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.db import connection
from django.dispatch import receiver

from zango.apps.accesslogs.models import AppAccessLog
from zango.apps.appauth.models import UserRoleModel
from zango.core.utils import get_current_request


@receiver(user_login_failed)
def login_failure_handler(sender, **kwargs):
    if connection.tenant.tenant_type == "app":
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
    if connection.tenant.tenant_type == "app":
        try:
            client_ip, is_routable = get_client_ip(request)
            if getattr(request, "user", None):
                username = (
                    request.user.email if request.user.email else request.user.mobile
                )
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
        except Exception:
            import traceback

            print(traceback.format_exc())


@receiver(user_logged_out)
def user_logged_out_handler(sender, user, **kwargs):
    if connection.tenant.tenant_type == "app":
        access_log = (
            AppAccessLog.objects.filter(user=user, session_expired_at__isnull=True)
            .order_by("-id")
            .first()
        )

        if access_log:
            access_log.session_expired_at = datetime.now()
            access_log.save()
