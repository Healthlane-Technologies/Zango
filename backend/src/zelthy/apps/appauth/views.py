from typing import Any
from django.urls import reverse
from django.shortcuts import redirect, render
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.core.exceptions import SuspiciousOperation

from formtools.wizard.views import SessionWizardView

from zelthy.core.generic_views.base import (
    ZelthySessionAppTemplateView,
    ZelthySessionAppView,
)
from zelthy.apps.appauth.login.utils import ZelthyLoginView
from zelthy.apps.appauth.models import UserRoleModel
from zelthy.apps.shared.tenancy.models import ThemesModel

from .login.forms import (
    AppLoginForm,
    UserRoleSelectionForm,
    AppUserResetPasswordForm,
    UserRoleSelectionForm,
    AppUserResetPasswordForm,
    ChangePasswordForm,
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
        app_theme_config = ThemesModel.objects.filter(
            tenant=self.request.tenant, is_active=True
        ).first()
        if app_theme_config:
            context["app_theme_config"] = app_theme_config
        return context

    def get_form_initial(self, step):
        initial = super(AppUserLoginView, self).get_form_initial(step)
        initial["request"] = self.request
        return initial

    def get_user(self):
        self.user_cache = super(AppUserLoginView, self).get_user()
        return self.user_cache


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


class AppUserChangePasswordView(ZelthySessionAppTemplateView, SessionWizardView):
    
    template_name = "applogin/change_password.html"

    form_list = (
        ("change_password", ChangePasswordForm),
    )

    def get_form_initial(self, step):
        initial = super(AppUserChangePasswordView, self).get_form_initial(step)
        initial["request"] = self.request
        initial["user"] = self.request.user
        return initial
    
    def get_context_data(self, form, **kwargs):
        context =  super(AppUserChangePasswordView, self).get_context_data(form, **kwargs)
        app_theme_config = ThemesModel.objects.filter(
            tenant=self.request.tenant, is_active=True
        ).first()
        if app_theme_config:
            context["app_theme_config"] = app_theme_config
        return context

    def done(self, form_list, **kwargs):
        form = form_list[0]
        form.save()
        return redirect("/app/home/")

    

