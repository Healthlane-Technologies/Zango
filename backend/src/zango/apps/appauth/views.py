from axes.decorators import axes_dispatch

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import View


@method_decorator(axes_dispatch, name="dispatch")
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
        if request.GET.get("redirect_url"):
            logout_url = request.GET.get("redirect_url")
        return redirect(logout_url)
