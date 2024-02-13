from django.urls import reverse
from django.shortcuts import redirect, render
from django.views.generic import View

from django.contrib.auth import logout
from django.core.exceptions import SuspiciousOperation


from zelthy.core.generic_views.base import (
    ZelthySessionAppTemplateView,
    ZelthySessionAppView,
)
from zelthy.apps.appauth.models import UserRoleModel
from zelthy.apps.shared.tenancy.models import ThemesModel



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
        logout_uri = "/login/"
        meta = request.META["HTTP_HOST"]
        logout_url = self.add_protocol(request, meta + logout_uri)
        if request.GET.get('redirect_url'):
            logout_url = request.GET.get('redirect_url')
        return redirect(logout_url)
