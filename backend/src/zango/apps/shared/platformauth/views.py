from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect


# Create your views here.
class PlatformUserLoginView(LoginView):
    """
    View to render the login page html.
    """

    template_name = "app_panel/app_panel_login.html"

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return redirect("/platform")


class PlatformUserLogoutView(LogoutView):
    """
    View to logout the user.
    """

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        return redirect("/auth/login")
