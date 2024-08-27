from axes.decorators import axes_dispatch

from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator


@method_decorator(axes_dispatch, name="dispatch")
# Create your views here.
class PlatformUserLoginView(LoginView):
    """
    View to render the login page html.
    """

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


@method_decorator(axes_dispatch, name="dispatch")
class PlatformUserLogoutView(LogoutView):
    """
    View to logout the user.
    """

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        return redirect("/auth/login")
