import json

from allauth.headless.account.views import ConfirmLoginCodeView, RequestLoginCodeView
from axes.handlers.proxy import AxesProxyHandler
from django_redis import get_redis_connection
from ipware import get_client_ip

from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.http import HttpResponse

from zango.apps.appauth.exceptions import OTPRateLimitExceeded
from zango.apps.appauth.models import AppUserModel, OTPCode
from zango.core.api import get_api_response
from zango.core.utils import generate_lockout_response


def _check_ip_rate_limit(request, otp_type):
    ip, _ = get_client_ip(request)
    if not ip:
        ip = "unknown"
    r = get_redis_connection("default")
    key = f"otp_gen_ip:{connection.schema_name}:{ip}:{otp_type}"
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, settings.OTP_IP_RATE_WINDOW, nx=True)
    count, _ = pipe.execute()
    if count > settings.OTP_IP_RATE_LIMIT:
        ttl = r.ttl(key)
        raise OTPRateLimitExceeded(
            f"Too many OTP requests. Try again in {ttl} seconds."
        )


class RequestLoginCodeViewAPIV1(RequestLoginCodeView):
    def handle(self, request, *args, **kwargs):
        auth_config = request.tenant.auth_config
        if (
            not auth_config.get("login_methods", {})
            .get("otp", {})
            .get("enabled", False)
        ):
            response = {
                "status": 400,
                "errors": [
                    {
                        "message": "OTP/Link login is not enabled",
                    }
                ],
            }
            return HttpResponse(json.dumps(response), status=400)

        try:
            _check_ip_rate_limit(request, "login_code")
        except OTPRateLimitExceeded as e:
            response = {
                "status": 429,
                "errors": [{"message": str(e)}],
            }
            return HttpResponse(json.dumps(response), status=429)

        query = Q()
        data = json.loads(request.body)
        email = data.get("email")
        phone = data.get("phone")
        if email:
            query = query | Q(email__iexact=email)
        if phone:
            query = query | Q(mobile=phone)
        try:
            user = AppUserModel.objects.get(query)
        except AppUserModel.DoesNotExist:
            response = {
                "status": 400,
                "errors": [
                    {
                        "message": "No account found with this email address.",
                    }
                ],
            }
            return HttpResponse(json.dumps(response), status=400)
        if not user.is_active:
            response = {
                "status": 400,
                "errors": [
                    {
                        "message": "Your account is currently inactive. Please reach out to support for assistance.",
                    }
                ],
            }
            return HttpResponse(json.dumps(response), status=400)
        if any(role.auth_config.get("enforce_sso", False) for role in user.roles.all()):
            response = {
                "status": 400,
                "errors": [
                    {"message": "OTP/Link login cannot be used when SSO is enforced"}
                ],
            }
            return HttpResponse(json.dumps(response), status=400)
        return super().handle(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            resp = super().post(request, *args, **kwargs)
        except OTPRateLimitExceeded as e:
            response = {
                "status": 429,
                "errors": [{"message": str(e)}],
            }
            return HttpResponse(json.dumps(response), status=429)
        resp_data = json.loads(resp.content.decode("utf-8"))
        if resp.status_code == 401:
            resp_data["data"]["message"] = "Verification code sent."
        return get_api_response(
            success=True,
            response_content=resp_data,
            status=resp.status_code,
        )


class ConfirmLoginCodeViewAPIV1(ConfirmLoginCodeView):
    def dispatch(self, request, *args, **kwargs):
        data = json.loads(request.body)
        code = data.get("code")

        # Resolve the target user (if any) so the axes lockout check also
        # covers the username+user_agent dimension, not just IP - axes
        # can't infer a username here on its own since this is a JSON body,
        # not a form post, so request.POST/request.data are both empty.
        otp_code = None
        credentials = {}
        if code:
            otp_code = OTPCode.objects.filter(code=code, otp_type="login_code").first()
            if otp_code:
                credentials = {settings.AXES_USERNAME_FORM_FIELD: otp_code.user.email}

        if not AxesProxyHandler.is_allowed(request, credentials):
            return generate_lockout_response(request, credentials)

        if code and otp_code:
            if not otp_code.is_valid():
                response = {
                    "status": 400,
                    "errors": [
                        {
                            "message": "Login code has expired or has already been used",
                        }
                    ],
                }
                return HttpResponse(json.dumps(response), status=400)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        return get_api_response(
            success=True,
            response_content=json.loads(resp.content.decode("utf-8")),
            status=resp.status_code,
        )
