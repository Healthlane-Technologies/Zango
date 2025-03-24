import json
import time
import uuid

import redis

from axes.decorators import axes_dispatch

from django.conf import settings
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views import View

from .constants import AZURE_URL, GOOGLE_URL


@method_decorator(axes_dispatch, name="dispatch")
# Create your views here.
class PlatformUserLoginView(LoginView):
    """
    View to render the login page html.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        OIDC_CONTEXT = {
            "enabled": settings.PLATFORM_AUTH_OIDC_ENABLE,
            "google": settings.PLATFORM_GOOGLE_OIDC_CONFIG,
            "azure": settings.PLATFORM_AZURE_OIDC_CONFIG,
        }
        context.update(OIDC_CONTEXT)
        return context

    def validate_oidc_config(self, oidc_context):
        # Check if OIDC_CONFIG is set correctly
        pass

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
        config_obj = self.get_openid_config(kwargs.get("slug"))

        nonce = self.set_nonce()
        state = {
            "target_url": query_params.get("redirect_url"),
            "provider": kwargs.get("slug"),
            "nonce": nonce,
        }

        client_id = config_obj.config["client_id"]
        redirect_url = "https://" + request.META["HTTP_HOST"] + "/openid/openid-router/"

        url = self.provider_url.get(config_obj.name)

        url = url.format(
            client_id=client_id,
            redirect_url=redirect_url,
            nonce=nonce,
            state=json.dumps(state),
        )
        return redirect(url)


@method_decorator(axes_dispatch, name="dispatch")
class PlatformUserLogoutView(LogoutView):
    """
    View to logout the user.
    """

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        return redirect("/auth/login")
