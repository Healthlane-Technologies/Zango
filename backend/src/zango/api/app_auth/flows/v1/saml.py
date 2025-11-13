import logging

from datetime import timedelta

from allauth.account.internal import flows
from allauth.account.models import Login
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from rest_framework.views import APIView

from django.contrib import messages
from django.core import signing
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from zango.apps.appauth.models import AppUserModel, SAMLModel, SAMLRequestId
from zango.apps.appauth.saml.utils import SAMLLoginMixin
from zango.core.api import get_api_response


logger = logging.getLogger(__name__)


def metadata(request, *args, **kwargs):
    saml_client_id = int(kwargs.get("saml_client_id", 0))
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
            user = AppUserModel.objects.get(email=email)
        except AppUserModel.DoesNotExist:
            return HttpResponseServerError("User does not exist")
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
            return HttpResponseRedirect("/app/login/")
        if resp.status_code == 302:
            if resp.url == "/app/login/":
                request.session.pop("saml", None)
                return HttpResponseRedirect("/app/login/")
            if "/role/set" in resp.url:
                roles = [
                    {"id": role_id, "name": role_name}
                    for role_id, role_name in user.roles.all().values_list("id", "name")
                ]
                print("Roles", roles)
                return HttpResponseRedirect(
                    f"/app/login/?next=role_selection&token={signing.dumps({'roles': roles}, key=in_response_to)}&request_id={in_response_to}"
                )
        return resp
    else:
        messages.add_message(
            request,
            messages.INFO,
            "Something went wrong. Please contact support if the problem persists!",
        )
        url = "/app/login/"
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
                        cUser = AppUserModel.objects.get(email__iexact=email)
                        if cUser.is_active:
                            result = {"is_valid": True, "message": "", "email": email}
                        else:
                            result = {
                                "is_valid": False,
                                "message": "The user account is not active. Please contact support.",
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
        saml_config = SAMLModel.objects.filter(id=self.request.data.get("saml_id", 0))
        if saml_config:
            return self.execute_sso_redirect(request, saml_config.first().id)
        else:
            return get_api_response(False, "No saml config", 400)
