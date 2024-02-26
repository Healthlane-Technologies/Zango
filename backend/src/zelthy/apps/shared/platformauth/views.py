from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from rest_framework.views import APIView
from zelthy.core.api import ZelthySessionPlatformAPIView, get_api_response


# Create your views here.
class PlatformUserLoginView(LoginView):
    """
    View to render the login page html.
    """

    template_name = "app_panel/app_panel_login.html"

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return redirect("/platform")


class PlatformUserLoginAPIV1(APIView):
    pass


class PlatformUserProfileAPIV1(ZelthySessionPlatformAPIView):
    """ """

    def get_profile_data(self, request):
        data = {}
        data["name"] = request.user.platform_user.name
        data["email"] = request.user.platform_user.email
        data["mobile"] = request.user.platform_user.mobile
        data["role"] = "Platform User"
        data["user_uuid"] = request.user.username
        return data

    def get(self, request, *args, **kwargs):
        data = self.get_profile_data(request)
        return get_api_response(True, data, 200)
