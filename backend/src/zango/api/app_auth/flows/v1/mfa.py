import json

from allauth.headless.base.views import APIView
from allauth.headless.mfa.views import AuthenticateView

from django.http import HttpResponse

from zango.apps.appauth.tasks import send_otp
from zango.core.api import get_api_response
from zango.core.utils import get_auth_priority, mask_email, mask_phone_number


class GetMFACodeViewAPIV1(APIView):
    def get_user(self, username):
        from django.db.models import Q

        from zango.apps.appauth.models import AppUserModel

        try:
            return AppUserModel.objects.get(Q(email=username) | Q(mobile=username))
        except AppUserModel.DoesNotExist:
            return None

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
                        "message": "MFA not required",
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

            if len(request.session.get("account_authentication_methods", [])) > 0:
                latest_auth_method = request.session["account_authentication_methods"][
                    0
                ]
                preferred_method = None

                request_data = {
                    "path": request.path,
                    "params": request.GET,
                }

                user = None
                if latest_auth_method.get("email"):
                    user = self.get_user(latest_auth_method.get("email"))
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
                    send_otp.delay(
                        method=preferred_method,
                        otp_type="two_factor_auth",
                        user_id=user.id,
                        tenant_id=request.tenant.id,
                        request_data=request_data,
                        user_role_id=request.session.get("role_id"),
                        message="Your 2FA code is {code}",
                    )
                else:
                    user = self.get_user(latest_auth_method.get("phone"))
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
                    send_otp.delay(
                        method=preferred_method,
                        otp_type="two_factor_auth",
                        user_id=user.id,
                        tenant_id=request.tenant.id,
                        request_data=request_data,
                        user_role_id=request.session.get("role_id"),
                        message="Your 2FA code is",
                        subject="2FA Verification Code",
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
                send_otp.delay(
                    method=preferred_method,
                    otp_type="two_factor_auth",
                    user_id=user.id,
                    tenant_id=request.tenant.id,
                    request_data=request_data,
                    user_role_id=request.session.get("role_id"),
                    message="Your 2FA code is {code}",
                    subject="2FA Verification Code",
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
