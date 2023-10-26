
from zelthy.core.api import get_api_response, ZelthyGenericAppAPIView

from .serializers import ProfileSerializer

class ProfileViewAPIV1(ZelthyGenericAppAPIView):
    def get(self, request, *args, **kwargs):
        serializer = ProfileSerializer(request.user)
        success = True
        response = {"message": "success", "profile_data": serializer.data}
        status = 200
        return get_api_response(success, response, status)
    
    def post(self, request, *args, **kwargs):
        serializer = ProfileSerializer(data=request.data, instance=request.user, partial=True)
        if serializer.is_valid():
            serializer.save()
            success = True
            response = {"message": "success"}
            status = 200
        else:
            success = False
            response = {"message": serializer.errors}
            status = 400
        return get_api_response(success, response, status)