from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from rest_framework.views import APIView
from zango.core.api import ZangoSessionPlatformAPIView, get_api_response


# Create your views here.
class PlatformUserLoginView(LoginView):
    """
    View to render the login page html.
    """

    template_name = "app_panel/app_panel_login.html"

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return redirect("/platform")
