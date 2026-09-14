import json

from allauth.headless.base.views import APIView
from allauth.headless.mfa.views import AuthenticateView

from django.http import HttpResponse

from zango.apps.appauth.tasks import send_otp
from zango.core.api import get_api_response
from zango.core.utils import get_auth_priority, mask_email, mask_phone_number

from .auth_utils import get_user_by_email_or_phone


class GetMFACodeViewAPIV1(APIView):
    def get_user(self, username):
        return get_user_by_email_or_phone(username)

    def get(self, request, *args, **kwargs):
        from allauth.account.internal.stagekit import unstash_login

        login = unstash_login(request, peek=True)
        policy = get_auth_priority(
            policy="two_factor_auth", request=request, user=login.user
        )
        if not policy.get("required"):
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": "MFA is not required",
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
        else:
            allowed_methods = policy.get("allowed_methods", [])
            if len(allowed_methods) == 0:
                resp = {
                    "status": 400,
                    "errors": [
                        {
                            "message": "No MFA methods configured",
                        }
                    ],
                }
                return HttpResponse(json.dumps(resp), status=400)

            from allauth.account.authentication import get_authentication_records

            # Get authentication records from the request
            auth_records = get_authentication_records(request)

            if auth_records and len(auth_records) > 0:
                # Get the latest authentication record
                latest_auth_record = auth_records[0]
                preferred_method = None

                request_data = {
                    "path": request.path,
                    "params": request.GET,
                }

                # Use login.user directly instead of fetching
                user = login.user
                if user is None:
                    resp = {
                        "status": 400,
                        "errors": [
                            {
                                "message": "User not found",
                            }
                        ],
                    }
                    return HttpResponse(json.dumps(resp), status=400)

                # Check if user authenticated with email
                if latest_auth_record.get("email"):
                    # If user authenticated with email, send OTP via SMS
                    preferred_method = "sms"
                    if preferred_method not in allowed_methods:
                        resp = {
                            "status": 400,
                            "errors": [
                                {
                                    "message": "SMS MFA method not allowed",
                                }
                            ],
                        }
                        return HttpResponse(json.dumps(resp), status=400)
                    hook = policy.get("sms_hook")
                    sms_content = policy.get("sms_content")
                    extra_data = policy.get("sms_extra_data")
                    config_key = policy.get("sms_config_key")
                    expiry = policy.get("expiry")

                    send_otp.delay(
                        method=preferred_method,
                        otp_type="two_factor_auth",
                        user_id=user.id,
                        tenant_id=request.tenant.id,
                        request_data=request_data,
                        user_role_id=request.session.get("role_id"),
                        message=sms_content
                        if sms_content
                        else "Your 2FA code is {code}",
                        hook=hook,
                        extra_data=extra_data,
                        config_key=config_key,
                        expiry=expiry,
                    )
                # Check if user authenticated with phone
                elif latest_auth_record.get("phone"):
                    # If user authenticated with phone, send OTP via email
                    preferred_method = "email"
                    if preferred_method not in allowed_methods:
                        resp = {
                            "status": 400,
                            "errors": [
                                {
                                    "message": "Email MFA method not allowed",
                                }
                            ],
                        }
                        return HttpResponse(json.dumps(resp), status=400)

                    email_content = policy.get("email_content")
                    config_key = policy.get("email_config_key")
                    hook = policy.get("email_hook")
                    subject = policy.get("email_subject")
                    expiry = policy.get("expiry")

                    send_otp.delay(
                        method=preferred_method,
                        otp_type="two_factor_auth",
                        user_id=user.id,
                        tenant_id=request.tenant.id,
                        request_data=request_data,
                        user_role_id=request.session.get("role_id"),
                        message=email_content
                        if email_content
                        else "Your 2FA code is {code}",
                        subject=subject if subject else "2FA Verification Code",
                        hook=hook,
                        expiry=expiry,
                        config_key=config_key,
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
            elif request.session.get("saml", False):
                # Handle SAML authentication
                preferred_method = "sms"
                if preferred_method not in allowed_methods:
                    resp = {
                        "status": 400,
                        "errors": [
                            {
                                "message": "SMS MFA method not allowed",
                            }
                        ],
                    }
                    return HttpResponse(json.dumps(resp), status=400)
                user = self.get_user(login.user.email)
                request_data = {
                    "path": request.path,
                    "params": request.GET,
                }

                hook = policy.get("sms_hook")
                sms_content = policy.get("sms_content")
                extra_data = policy.get("sms_extra_data")
                config_key = policy.get("sms_config_key")
                expiry = policy.get("expiry")

                send_otp.delay(
                    method=preferred_method,
                    otp_type="two_factor_auth",
                    user_id=user.id,
                    tenant_id=request.tenant.id,
                    request_data=request_data,
                    user_role_id=request.session.get("role_id"),
                    message=sms_content if sms_content else "Your 2FA code is {code}",
                    hook=hook,
                    extra_data=extra_data,
                    config_key=config_key,
                    expiry=expiry,
                )
                return get_api_response(
                    success=True,
                    response_content={
                        "message": f"Verification code sent to {preferred_method}",
                        "masked_destination": mask_phone_number(str(user.mobile)),
                    },
                    status=200,
                )
            else:
                resp = {
                    "status": 400,
                    "errors": [
                        {
                            "message": "User not authenticated",
                        }
                    ],
                }
                return HttpResponse(json.dumps(resp), status=400)


class MFAVerifyViewAPIV1(AuthenticateView):
    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        return get_api_response(
            success=True,
            response_content=json.loads(resp.content.decode("utf-8")),
            status=resp.status_code,
        )
