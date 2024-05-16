from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.contrib.auth import logout
from rest_framework.views import APIView


# Create your views here.
class PlatformUserLoginView(LoginView):
    """
    View to render the login page html.
    """

    template_name = "app_panel/app_panel_login.html"

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return redirect("/platform")


class PlatformUserLogoutView(APIView):
    """
    View to logout the user.
    """

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("/auth/login")
