import json

from datetime import timedelta

from allauth.account.internal import flows
from allauth.account.models import Login
from allauth.headless.base.response import AuthenticationResponse
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from rest_framework.views import APIView

from django.core import signing
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from zango.apps.appauth.models import AppUserModel, SAMLModel, SAMLRequestId
from zango.apps.appauth.saml.utils import SAMLLoginMixin
from zango.core.api import get_api_response
from zango.core.utils import get_auth_priority


def metadata(request, *args, **kwargs):
    saml_client_id = int(kwargs.get("saml_client_id", 0))
    try:
        saml_config = SAMLModel.objects.get(id=saml_client_id)
        if not saml_config.is_active:
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": "SAML is not active for this provider",
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
    except SAMLModel.DoesNotExist:
        resp = {
            "status": 400,
            "errors": [
                {
                    "message": "No saml config found for the given client ID",
                }
            ],
        }
        return HttpResponse(json.dumps(resp), status=400)
    _settings = SAMLModel.objects.get(id=saml_client_id).get_settings_dict()
    saml_settings = OneLogin_Saml2_Settings(
        settings=_settings, custom_base_path=None, sp_validation_only=True
    )
    metadata = saml_settings.get_sp_metadata()
    errors = saml_settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = HttpResponse(content=metadata, content_type="text/xml")
    else:
        resp = HttpResponseServerError(content=", ".join(errors))
    return resp


@csrf_exempt
def acs(request, *args, **kwargs):
    saml_client_id = int(kwargs.get("saml_client_id", 0))
    try:
        saml_config = SAMLModel.objects.get(id=saml_client_id)
        if not saml_config.is_active:
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": "SAML is not active for this provider",
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
    except SAMLModel.DoesNotExist:
        resp = {
            "status": 400,
            "errors": [
                {
                    "message": "No saml config found for the given client ID",
                }
            ],
        }
        return HttpResponse(json.dumps(resp), status=400)
    s = SAMLLoginMixin()
    req = s.prepare_request_for_saml(request)
    auth = s.init_saml_auth(req, saml_client_id)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False
    request_id = None
    response = auth.login()
    in_response_to = s.get_in_response_to(request, saml_client_id)
    if "AuthNRequestID" in request.session:
        request_id = request.session["AuthNRequestID"]
    auth.process_response(request_id=request_id)
    errors = auth.get_errors()
    not_auth_warn = not auth.is_authenticated()

    if not errors and auth.is_authenticated():
        email = auth.get_nameid()
        try:
            user = AppUserModel.objects.get(email__iexact=email)
        except AppUserModel.DoesNotExist:
            resp = {
                "message": "User does not exist",
                "code": "user_not_found",
                "param": "email",
            }
            return HttpResponseRedirect(
                redirect_to=f"/app/login/?token={signing.dumps(resp, key=in_response_to)}&request_id={in_response_to}"
            )
        request.session["saml"] = True
        login = Login(
            user=user,
            email_verification=False,
            redirect_url="/app/login/",
            signal_kwargs={},
            signup=False,
            email=email,
        )
        login.user = user

        resp = flows.login.perform_login(request, login)
        if resp.status_code == 200:
            request.session.pop("saml", None)
        enhanced_resp = AuthenticationResponse(request)
        resp_data = json.loads(enhanced_resp.content.decode("utf-8"))
        return HttpResponseRedirect(
            f"/app/login/?token={signing.dumps(resp_data, key=in_response_to)}&request_id={in_response_to}"
        )
    else:
        url = f"/app/login/?token={signing.dumps({'error': errors}, key=in_response_to)}&request_id={in_response_to}"
        return HttpResponseRedirect(url)


class SAMLOpsApi(APIView, SAMLLoginMixin):
    def get(self, request, *args, **kwargs):
        action = request.GET.get("action", "")
        last_requests = []
        if action == "request_id":
            request_id = request.GET.get("request_id", "")
            token = request.GET.get("token", "")
            last_requests = SAMLRequestId.objects.filter(
                request_id=request_id,
                created_at__gte=timezone.now() - timedelta(minutes=10),
            )
            if len(last_requests) > 0:
                try:
                    email = signing.loads(token, key=request_id, max_age=300)
                    try:
                        user = AppUserModel.objects.get(email__iexact=email)
                        if user.is_active:
                            result = {"is_valid": True, "message": "", "email": email}
                        else:
                            result = {
                                "is_valid": False,
                                "message": "Your account is currently inactive. Please reach out to support for assistance.",
                                "email": None,
                            }

                    except Exception:
                        result = {
                            "is_valid": False,
                            "message": "The user is not registered. Please contact support.",
                            "email": None,
                        }
                except Exception:
                    result = {
                        "is_valid": False,
                        "message": "This request is not valid. Please try again.",
                        "email": None,
                    }
                return get_api_response(True, result, 200)
        elif action == "delete_request_id":
            email = request.GET.get("email", "")
            request_id = request.GET.get("request_id", "")
            SAMLRequestId.objects.filter(request_id=request_id).delete()
            return get_api_response(True, "request deleted", 200)
        elif action == "get_metadata":
            token = request.GET.get("token", "")
            request_id = request.GET.get("request_id", "")
            meta = signing.loads(token, key=request_id, max_age=300)
            return get_api_response(True, meta, 200)
        return get_api_response(False, "error", 400)


class SAMLLoginInitViewV1(APIView, SAMLLoginMixin):
    def post(self, request, *args, **kwargs):
        login_methods = get_auth_priority(policy="login_methods", request=request)
        if login_methods["sso"]["enabled"] is False:
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": "SAML is not enabled",
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
        saml_id = self.request.data.get("saml_id", None)
        if not saml_id:
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": "SAML ID is required",
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
        try:
            saml_config = SAMLModel.objects.get(id=saml_id)
            if not saml_config.is_active:
                resp = {
                    "status": 400,
                    "errors": [
                        {
                            "message": "SAML is not active for this provider",
                        }
                    ],
                }
                return HttpResponse(json.dumps(resp), status=400)
            return self.execute_sso_redirect(request, saml_config.id)
        except SAMLModel.DoesNotExist:
            resp = {
                "status": 400,
                "errors": [
                    {
                        "message": "No saml config found for the given client ID",
                    }
                ],
            }
            return HttpResponse(json.dumps(resp), status=400)
