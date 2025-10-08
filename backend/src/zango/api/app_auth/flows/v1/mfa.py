import json

from allauth.headless.base.views import APIView
from allauth.headless.mfa.views import AuthenticateView

from zango.apps.appauth.tasks import send_otp
from zango.core.api import get_api_response
from zango.core.utils import get_auth_priority, mask_email, mask_phone_number


class GetMFACodeViewAPIV1(APIView):
    def get(self, request, *args, **kwargs):
        from allauth.account.internal.stagekit import unstash_login

        login = unstash_login(request, peek=True)
        if not login:
            return get_api_response(
                success=False,
                response_content={"message": "User not logged in"},
                status=400,
            )
        user = login.user
        request_data = {
            "path": request.path,
            "params": request.GET,
        }
        policy = get_auth_priority(
            policy="two_factor_auth", request=request, user=login.user
        )
        if not isinstance(policy, dict) or not policy.get("required"):
            return get_api_response(
                success=False,
                response_content={"message": "MFA not required"},
                status=400,
            )
        else:
            allowed_methods = (
                policy.get("allowed_methods", []) if isinstance(policy, dict) else []
            )
            if len(allowed_methods) == 0:
                return get_api_response(
                    success=False,
                    response_content={"message": "No MFA methods configured"},
                    status=400,
                )

            if len(request.session.get("account_authentication_methods", [])) > 0:
                latest_auth_method = request.session["account_authentication_methods"][
                    0
                ]
                preferred_method = None

                if latest_auth_method.get("email"):
                    preferred_method = "sms"
                    if preferred_method not in allowed_methods:
                        return get_api_response(
                            success=False,
                            response_content={"message": "SMS MFA method not allowed"},
                            status=400,
                        )
                    sms_extra_data = (
                        policy.get("sms_extra_data")
                        if isinstance(policy, dict)
                        else None
                    )
                    if sms_extra_data and isinstance(sms_extra_data, str):
                        try:
                            sms_extra_data = json.loads(sms_extra_data)
                        except (json.JSONDecodeError, ValueError):
                            sms_extra_data = {}

                    send_otp.delay(
                        method=preferred_method,
                        otp_type="two_factor_auth",
                        user_id=user.id,
                        tenant_id=request.tenant.id,
                        request_data=request_data,
                        user_role_id=request.session.get("role_id"),
                        message=(
                            policy.get("sms_content")
                            if isinstance(policy, dict)
                            else None
                        )
                        or "Your 2FA code is {code}",
                        hook=policy.get("sms_hook")
                        if isinstance(policy, dict)
                        else None,
                        config_key=policy.get("sms_config_key")
                        if isinstance(policy, dict)
                        else None,
                        extra_data=sms_extra_data,
                    )
                else:
                    preferred_method = "email"
                    if preferred_method not in allowed_methods:
                        return get_api_response(
                            success=False,
                            response_content={
                                "message": "Email MFA method not allowed"
                            },
                            status=400,
                        )
                    send_otp.delay(
                        method=preferred_method,
                        otp_type="two_factor_auth",
                        user_id=user.id,
                        tenant_id=request.tenant.id,
                        request_data=request_data,
                        user_role_id=request.session.get("role_id"),
                        message=(
                            policy.get("email_content")
                            if isinstance(policy, dict)
                            else None
                        )
                        or "Your 2FA code is {code}",
                        subject=(
                            policy.get("email_subject")
                            if isinstance(policy, dict)
                            else None
                        )
                        or "2FA Verification Code",
                        hook=policy.get("email_hook")
                        if isinstance(policy, dict)
                        else None,
                        config_key=policy.get("email_config_key")
                        if isinstance(policy, dict)
                        else None,
                    )
                return get_api_response(
                    success=True,
                    response_content={
                        "message": f"Verification code sent to {preferred_method}",
                        "masked_destination": mask_email(user.email)
                        if preferred_method == "email"
                        else mask_phone_number(str(user.mobile)),
                    },
                    status=200,
                )
            elif request.session.get("sociallogin"):
                send_otp.delay(
                    method="email",
                    otp_type="two_factor_auth",
                    user_id=user.id,
                    tenant_id=request.tenant.id,
                    request_data=request_data,
                    user_role_id=request.session.get("role_id"),
                    message=(
                        policy.get("email_content")
                        if isinstance(policy, dict)
                        else None
                    )
                    or "Your 2FA code is {code}",
                    subject=(
                        policy.get("email_subject")
                        if isinstance(policy, dict)
                        else None
                    )
                    or "2FA Verification Code",
                    hook=policy.get("email_hook") if isinstance(policy, dict) else None,
                    config_key=policy.get("email_config_key")
                    if isinstance(policy, dict)
                    else None,
                )
                return get_api_response(
                    success=True,
                    response_content={
                        "message": "Verification code sent to email",
                        "masked_destination": mask_email(user.email),
                    },
                    status=200,
                )
            else:
                return get_api_response(
                    success=False,
                    response_content={"message": "User not authenticated"},
                    status=400,
                )


class MFAVerifyViewAPIV1(AuthenticateView):
    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        return get_api_response(
            success=True,
            response_content=json.loads(resp.content.decode("utf-8")),
            status=resp.status_code,
        )
