import requests

from celery import shared_task


@shared_task
def send_otp(method, otp_type, user_id, tenant_id, request_data, user_role_id):
    try:
        from django.db import connection

        from zango.apps.appauth.models import AppUserModel, UserRoleModel, generate_otp
        from zango.apps.shared.tenancy.models import TenantModel
        from zango.core.utils import (
            get_auth_priority,
            get_mock_request,
            get_package_url,
        )

        tenant = TenantModel.objects.get(id=tenant_id)
        connection.set_tenant(tenant)

        request = get_mock_request(path=request_data.get("path"))
        request.META = {"HTTP_HOST": tenant.get_primary_domain()}
        user = AppUserModel.objects.get(id=user_id)
        user_role = UserRoleModel.objects.get(id=user_role_id)
        request.user = user
        if otp_type == "two_factor_auth":
            policy = get_auth_priority(
                policy="two_factor_auth",
                request=request,
                user=user,
                user_role=user_role,
                tenant=tenant,
            )
            if policy.get("required", False):
                twofa = generate_otp(user, otp_type)
                message = f"Your verification code is {twofa}"
                if method == "email":
                    email_config = policy.get("email", {})
                    url = email_config.get("url")
                    if not url:
                        url = get_package_url(
                            request, "email/api/?action=send", "communication"
                        )
                    resp = requests.post(
                        url,
                        data={
                            "body": message,
                            "to": user.email,
                            "subject": "Verification Code",
                        },
                    )
                    resp.raise_for_status()
                elif method == "sms":
                    sms_config = policy.get("sms", {})
                    url = sms_config.get("url")
                    if not url:
                        url = get_package_url(
                            request, "sms/api/?action=send", "communication"
                        )
                    resp = requests.post(
                        url, data={"message": message, "to": str(user.mobile)}
                    )
                    resp.raise_for_status()
    except Exception as e:
        import traceback

        return {
            "success": False,
            "message": traceback.format_exc(),
        }
