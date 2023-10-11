from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.core.exceptions import SuspiciousOperation

from zelthy.core.generic_views.base import (
    ZelthySessionAppTemplateView,
    ZelthySessionAppView,
)
from zelthy.apps.appauth.login.utils import ZelthyLoginView
from zelthy.apps.appauth.models import UserRoleModel

from .login.forms import (
    AppLoginForm,
    UserRoleSelectionForm,
    AppUserResetPasswordForm,
    UserRoleSelectionForm,
    AppUserResetPasswordForm,
)


@method_decorator(csrf_exempt, name="dispatch")
class AppUserLoginView(ZelthyLoginView):
    """
    View to render the login page html.
    """

    template_name = "applogin/login.html"  # To be updated with new html

    userrolemodel = UserRoleModel

    form_list = (
        ("auth", AppLoginForm),
        ("user_role", UserRoleSelectionForm),
        ("password_reset", AppUserResetPasswordForm),
    )

    def get_context_data(self, **kwargs):
        context = super(AppUserLoginView, self).get_context_data(**kwargs)
        context["tenant"] = self.request.tenant
        return context

    def get_form_initial(self, step):
        initial = super(AppUserLoginView, self).get_form_initial(step)
        initial["request"] = self.request
        return initial

    def get_user(self):
        self.user_cache = super(AppUserLoginView, self).get_user()
        return self.user_cache


class AppUserLandingView(ZelthySessionAppTemplateView):
    """
    View to render the landing page after login.
    """

    template_name = "applandingPage.html"  # To be updated with new html

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SwitchUserRoleView(ZelthySessionAppView):
    def get(self, request, *args, **kwargs):
        role_id = kwargs["role_id"]
        if not request.user.roles.filter(id=role_id).exists():
            raise SuspiciousOperation(
                "Trying to apply role for which is not mapped to user"
            )
        request.session["role_id"] = role_id
        return redirect("/app/home/")


class AppLogoutView(View):
    def add_protocol(self, request, url):
        if request.is_secure():
            full_url = "https://" + url
        else:
            full_url = "http://" + url
        return full_url

    def get(self, request, *args, **kwargs):
        logout(request)
        logout_uri = reverse("app-login-view")
        meta = request.META["HTTP_HOST"]
        logout_url = self.add_protocol(request, meta + logout_uri)
        return redirect(logout_url)
