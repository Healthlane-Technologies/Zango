import json
import time
import uuid

import redis
import requests

from axes.decorators import axes_dispatch

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.core import signing
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.templatetags.static import static
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from zango.apps.shared.platformauth.models import PlatformUserModel
from zango.core.api import get_api_response
from zango.core.decorators import internal_access_only

from .constants import AZURE_URL, GOOGLE_OAUTH_BASE_URL, GOOGLE_URL
from .utils import OpenIDValidator


USER_AUTH_BACKEND = (
    "zango.apps.shared.platformauth.auth_backend.PlatformUserModelBackend"
)


def get_current_domain(request):
    return "https://" + request.META["HTTP_HOST"]


def get_openid_config(provider):
    if provider == "google":
        return {
            "client_id": settings.GOOGLE_OIDC_CLIENT_ID,
            "client_secret": settings.GOOGLE_OIDC_CLIENT_SECRET,
        }
    if provider == "azure":
        return {
            "client_id": settings.AZURE_OIDC_CLIENT_ID,
            "client_secret": settings.AZURE_OIDC_CLIENT_SECRET,
        }
    raise ValueError("Invalid Provider")


@method_decorator([axes_dispatch, internal_access_only], name="dispatch")
# Create your views here.
class PlatformUserLoginView(LoginView):
    """
    View to render the login page html.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        oidc_context_data = {
            "enabled": getattr(settings, "PLATFORM_AUTH_OIDC_ENABLE", False),
            "google": {
                "enabled": getattr(settings, "GOOGLE_OIDC_ENABLE", False),
                "image_url": static("app_panel/images/googleLogin.svg"),
            },
            "azure": {
                "enabled": getattr(settings, "AZURE_OIDC_ENABLE", False),
                "image_url": static("app_panel/images/azureLogin.svg"),
            },
            "oidc_url": "/auth/openid/initiate/",
        }
        if (
            not oidc_context_data["google"]["enabled"]
            and not oidc_context_data["azure"]["enabled"]
        ):
            oidc_context_data["enabled"] = False
        context["oidc_context"] = oidc_context_data
        return context

    template_name = "app_panel/app_panel_login.html"

    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        if resp.status_code == 302:
            return redirect("/platform")
        else:
            context = self.get_context_data()
            context["error_message"] = (
                "Please enter a correct email address and password. Note that both fields may be case-sensitive."
            )
            return TemplateResponse(request, self.template_name, context)


@method_decorator(internal_access_only, name="dispatch")
class OpenIDInitiateView(View):
    """
    OpenID workflow; Triggered when OpenID provider is selected on the login page
    Generates the provider's authorization url and redirects the user to it.
    """

    provider_url = {"azure": AZURE_URL, "google": GOOGLE_URL}

    def set_nonce(self):
        """
        Generates a nonce value using UUID, sets an expiry time, and stores it in Redis.

        Returns:
            str: The generated nonce value.
        """
        nonce = str(uuid.uuid4())
        r = redis.from_url(settings.REDIS_URL)
        expiry_at = time.time() + 600  # expire in 10 mins
        r.hmset(nonce, {"expiry_at": expiry_at})
        return nonce

    def get(self, request, *args, **kwargs):
        query_params = self.request.GET
        provider = kwargs.get("provider")
        config_obj = get_openid_config(provider)

        nonce = self.set_nonce()
        state = {
            "target_url": query_params.get("redirect_url"),
            "provider": provider,
            "nonce": nonce,
        }

        client_id = config_obj["client_id"]
        redirect_url = get_current_domain(request) + "/auth/openid/router/"

        url = self.provider_url.get(provider)

        url = url.format(
            client_id=client_id,
            redirect_url=redirect_url,
            nonce=nonce,
            state=json.dumps(state),
        )
        return get_api_response(
            success=True, response_content={"redirect_url": url}, status=200
        )


@method_decorator(csrf_exempt, name="dispatch")
class OpenIDValidationView(View):
    """
    View for handling Single Sign-On (SSO) login.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.provider_functions = {
            "google": self._get_google_id_token,
            "azure": self._get_azure_id_token,
        }

    def _get_google_id_token(self, config):
        """
        Retrieves the Google ID token by making a POST request to the Google OAuth token endpoint.

        Args:
            config (dict): A dictionary containing the client ID and client secret for the Google OAuth client.

        Returns:
            str: The Google ID token.

        Raises:
            requests.exceptions.RequestException: If there is an error making the POST request.
        """

        data = {
            "code": self.request.GET.get("code"),
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "redirect_uri": get_current_domain(self.request) + "/auth/openid/router/",
            "grant_type": "authorization_code",
        }
        response = requests.post(GOOGLE_OAUTH_BASE_URL + "token", data=data)
        response = response.json()
        id_token = response["id_token"]
        return id_token

    def _get_azure_id_token(self, config):
        """
        Get the Azure ID token from the request POST data.

        Args:
            config (dict): The configuration for the Azure ID token.

        Returns:
            str: The Azure ID token.
        """
        id_token = self.request.POST.get("id_token")
        return id_token

    def get_validation(self, provider, id_token):
        """
        A function to validate the OpenID token for a given provider.

        Args:
            provider_slug (str): The unique identifier for the provider.
            id_token (str): The OpenID token to validate.

        Returns:
            dict: A dictionary containing the validation result, message, and email.
                - is_valid (bool): Indicates if the token is valid.
                - message (str): A message related to the validation result.
                - email (str or None): The email retrieved from the token, if valid.
        """

        provider_config = get_openid_config(provider)

        validator_obj = OpenIDValidator(provider_config, id_token, provider)
        if validator_obj.is_validated():
            email = validator_obj.get_username()
            if email:
                return {"is_valid": True, "message": "", "email": email}
            else:
                return {
                    "is_valid": False,
                    "message": "Failed to retrieve email. Please try again later.",
                    "email": None,
                }
        else:
            return {
                "is_valid": False,
                "message": "Validation failed, please try again!",
                "email": None,
            }

    def encrypt_email(self, email):
        """
        Encrypt the email using Django's signing module.

        Args:
            email (str): The email to encrypt.

        Returns:
            str or None: The encrypted email, or None if encryption fails.
        """
        try:
            email = signing.dumps(email)
            return email
        except Exception:
            return None

    def get_id_token(self, provider):
        """
        Retrieves the ID token for the specified OpenID provider.

        Args:
            provider_slug (str): The slug of the OpenID provider.

        Returns:
            str or None: The ID token, or None if not found.
        """

        config = get_openid_config(provider)

        id_token = self.provider_functions.get(provider)(config)

        return id_token if id_token else None

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests for the OpenID login flow.
        """

        state = json.loads(self.request.GET.get("state", "{}"))
        return self.handle_openid_flow(
            request, state
        )  # Call the common handler for GET requests

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests, particularly for Azure.
        """

        state = json.loads(self.request.POST.get("state", "{}"))
        return self.handle_openid_flow(
            request, state
        )  # Call the common handler for POST requests

    def handle_openid_flow(self, request, state):
        """
        Common method to handle the OpenID flow for both GET and POST requests.

        This method processes the frlow, retrieves the ID token, validates it,
        and redirects the user to the appropriate URL based on the outcome.
        """
        current_domain_url = get_current_domain(self.request)

        try:
            provider = state.get("provider")
            # Retrieve the ID token based on the provider
            id_token = self.get_id_token(provider)

            # Validate the token and handle the response accordingly
            validation = self.get_validation(provider, id_token)
            if validation["is_valid"]:
                encoded_data = self.encrypt_email(validation["email"])
                url = (
                    current_domain_url + state["target_url"] + f"?token={encoded_data}"
                )
            else:
                url = current_domain_url + state["target_url"]
            return HttpResponseRedirect(url)

        except Exception as e:
            import traceback

            traceback.print_exc()
            url = current_domain_url + state.get(
                "target_url", "/auth/login/"
            )  # Default to login page on error
            return HttpResponseRedirect(url)


@method_decorator([axes_dispatch, internal_access_only], name="dispatch")
class AppOpenIDLogin(LoginView):
    """
    View to signin into the platform
    """

    def get_email(self):
        token = self.request.GET.get("token")
        try:
            email = signing.loads(token)
            return email
        except Exception:
            return None

    def get_user(self):
        email = self.get_email()
        if email:
            try:
                user = PlatformUserModel.objects.get(
                    email__iexact=email, is_active=True
                )
                return user.user
            except PlatformUserModel.DoesNotExist:
                # Case where the user does not exist
                return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_user()
        """ This flag indicates whether the user exists"""
        context["user_validated"] = user is not None

        return context

    def get(self, request, *args, **kwargs):
        url = "/auth/login/"
        user = self.get_user()
        if user and user.is_active:
            login(request, user, backend=USER_AUTH_BACKEND)
            redirect_to = "/platform/apps/"
            response = redirect(redirect_to)
            return response
        return HttpResponseRedirect(url)


@method_decorator([axes_dispatch, internal_access_only], name="dispatch")
class PlatformUserLogoutView(LogoutView):
    """
    View to logout the user.
    """

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        return redirect("/auth/login")
