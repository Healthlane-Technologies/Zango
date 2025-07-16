import json

from allauth.headless.mfa.views import AuthenticateView
from rest_framework.views import APIView

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
        policy = get_auth_priority(policy="two_factor_auth", request=request)
        if not policy.get("required"):
            return get_api_response(
                success=False,
                response_content={"message": "MFA not required"},
                status=400,
            )
        else:
            allowed_methods = policy.get("allowed_methods", [])
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

                request_data = {
                    "path": request.path,
                    "params": request.GET,
                }

                user = None
                if latest_auth_method.get("email"):
                    user = self.get_user(latest_auth_method.get("email"))
                    if user is None:
                        return get_api_response(
                            success=False,
                            response_content={"message": "User not found"},
                            status=400,
                        )
                    preferred_method = "sms"
                    if preferred_method not in allowed_methods:
                        return get_api_response(
                            success=False,
                            response_content={"message": "SMS MFA method not allowed"},
                            status=400,
                        )
                    send_otp.delay(
                        preferred_method,
                        "two_factor_auth",
                        user.id,
                        request.tenant.id,
                        request_data,
                        request.session.get("role_id"),
                    )
                else:
                    user = self.get_user(latest_auth_method.get("phone"))
                    if user is None:
                        return get_api_response(
                            success=False,
                            response_content={"message": "User not found"},
                            status=400,
                        )
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
                        preferred_method,
                        "two_factor_auth",
                        user.id,
                        request.tenant.id,
                        request_data,
                        request.session.get("role_id"),
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
            success=True if resp.status_code == 200 else False,
            response_content=json.loads(resp.content.decode("utf-8")),
            status=resp.status_code,
        )
