from zango.apps.appauth.models import AppUserAuthToken
from zango.apps.appauth.serializers import AppUserAuthTokenSerializer
from zango.core.api import (
    ZangoGenericAppAPIView,
    get_api_response,
)

from .serializers import ProfileSerializer


class ProfileViewAPIV1(ZangoGenericAppAPIView):
    def get(self, request, *args, **kwargs):
        serializer = ProfileSerializer(request.user, context={"request": request})
        success = True
        tokens = AppUserAuthToken.objects.filter(user=request.user)
        token_serializer = AppUserAuthTokenSerializer(
            tokens, many=True, context={"request": request, "tenant": request.tenant}
        )
        response = {
            "message": "success",
            "profile_data": serializer.data,
            "tokens": token_serializer.data,
        }
        status = 200
        return get_api_response(success, response, status)

    def put(self, request, *args, **kwargs):
        profile_image = request.FILES.get("profile_pic")
        response = request.user.update_user(request.data, profile_image=profile_image)
        success = response.pop("success")
        if success:
            status = 200
        else:
            status = 400
        return get_api_response(success, response, status)
