from zango.apps.appauth.models import AppUserAuthToken
from zango.apps.appauth.serializers import AppUserAuthTokenSerializer
from zango.core.api import (
    ZangoGenericAppAPIView,
    get_api_response,
)
from zango.core.utils import get_auth_priority, get_current_role

from .serializers import ProfileSerializer


class ProfileViewAPIV1(ZangoGenericAppAPIView):
    def can_set_password(self, request):
        login_methods = get_auth_priority(policy="login_methods", request=request)
        if not login_methods.get("password", {}).get("enabled", False):
            return False
        if any(
            role.auth_config.get("enforce_sso", False)
            for role in request.user.roles.all()
        ):
            return False
        return True

    def get(self, request, *args, **kwargs):
        serializer = ProfileSerializer(
            request.user, context={"request": request, "tenant": request.tenant}
        )
        success = True
        tokens = AppUserAuthToken.objects.filter(user=request.user)
        token_serializer = AppUserAuthTokenSerializer(
            tokens, many=True, context={"request": request, "tenant": request.tenant}
        )
        role = get_current_role()
        can_set_password = self.can_set_password(request)
        response = {
            "message": "success",
            "profile_data": serializer.data,
            "should_set_password": request.user.has_usable_password() is False
            and can_set_password,
            "can_set_password": can_set_password,
            "current_role": {
                "id": role.id,
                "name": role.name,
            },
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
