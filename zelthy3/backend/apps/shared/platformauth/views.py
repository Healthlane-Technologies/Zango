from django.shortcuts import render
from django.views.generic.base import TemplateView
from rest_framework.views import APIView
from backend.core.api import ZelthySessionPlatformAPIView, get_api_response



# Create your views here.
class PlatformUserLoginView(TemplateView):
    """
    View to render the login page html.
    """
    template_name = 'platform_login.html'


class PlatformUserLoginAPIV1(APIView):
    pass


class PlatformUserProfileAPIV1(ZelthySessionPlatformAPIView):
    """
    
    """
    def get_profile_data(self, request):
        data = {}
        data['name'] = request.user.platform_user.name
        data['email'] = request.user.platform_user.email
        data['mobile'] = request.user.platform_user.mobile
        data['role'] = 'Platform User'
        data['user_uuid'] = request.user.username
        return data

    def get(self, request, *args, **kwargs):
        data = self.get_profile_data(request)
        return get_api_response(True, data, 200)