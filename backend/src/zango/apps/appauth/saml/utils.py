from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.response import OneLogin_Saml2_Response
from onelogin.saml2.settings import OneLogin_Saml2_Settings

from zango.apps.appauth.models import SAMLModel, SAMLRequestId
from zango.core.api import get_api_response


class SAMLLoginMixin(object):
    def get_settings_dict(self, saml_client_id):
        _settings = SAMLModel.objects.get(id=saml_client_id).get_settings_dict()
        return _settings

    def get_saml_settings(self, saml_client_id):
        return OneLogin_Saml2_Settings(
            settings=self.get_settings_dict(saml_client_id),
            custom_base_path=None,
            sp_validation_only=True,
        )

    def get_in_response_to(self, request, saml_client_id):
        res_obj = OneLogin_Saml2_Response(
            self.get_saml_settings(saml_client_id), request.POST["SAMLResponse"]
        )
        return res_obj.document.get("InResponseTo", None)

    def init_saml_auth(self, request, saml_client_id):
        auth = OneLogin_Saml2_Auth(
            request, old_settings=self.get_settings_dict(saml_client_id)
        )
        return auth

    def prepare_request_for_saml(self, request):
        # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
        result = {
            "https": "on" if request.is_secure() else "off",
            "http_host": request.META["HTTP_HOST"],
            "script_name": request.META["PATH_INFO"],
            "server_port": request.META["SERVER_PORT"],
            "get_data": request.GET.copy(),
            "post_data": request.POST.copy(),
            "query_string": request.META["QUERY_STRING"],
        }
        return result

    def execute_sso_redirect(self, request, saml_client_id):
        req = self.prepare_request_for_saml(request)
        auth = self.init_saml_auth(req, saml_client_id)
        errors = []
        error_reason = None
        not_auth_warn = False
        success_slo = False
        attributes = False
        paint_logout = False
        url = auth.login()
        SAMLRequestId.objects.create(request_id=auth.get_last_request_id())
        return get_api_response(True, url, 200)
