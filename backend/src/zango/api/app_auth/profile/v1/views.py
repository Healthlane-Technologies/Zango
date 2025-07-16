from zango.core.api import (
    ZangoGenericAppAPIView,
    get_api_response,
)

from .serializers import ProfileSerializer


class ProfileViewAPIV1(ZangoGenericAppAPIView):
    def get(self, request, *args, **kwargs):
        serializer = ProfileSerializer(request.user)
        success = True
        response = {"message": "success", "profile_data": serializer.data}
        status = 200
        return get_api_response(success, response, status)

    def put(self, request, *args, **kwargs):
        response = request.user.update_user(request.data)
        success = response.pop("success")
        if success:
            status = 200
        else:
            status = 400
        return get_api_response(success, response, status)
