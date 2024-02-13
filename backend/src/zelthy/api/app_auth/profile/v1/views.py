from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from zelthy.core.api import (
    get_api_response,
    ZelthyGenericAppAPIView,
    ZelthySessionAppAPIView,
)
from zelthy.api.app_auth.profile.v1.utils import PasswordValidationMixin
from zelthy.apps.appauth.models import OldPasswords

from .serializers import ProfileSerializer


class ProfileViewAPIV1(ZelthyGenericAppAPIView):
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


class PasswordChangeViewAPIV1(ZelthySessionAppAPIView, PasswordValidationMixin):
    def clean_password(self, email, password):
        """
        Validates that the email is not already in use.
        """
        try:
            user = authenticate(username=email, password=password)
        except:
            raise ValidationError(
                "The current password you have entered is wrong. Please try again!"
            )

    def clean_password2(self, user, current_password, new_password):
        """method to validate password"""
        password2 = new_password
        validation = self.run_all_validations(
            user, new_password, password2, current_password
        )
        if not validation.get("validation"):
            raise ValidationError(validation.get("msg"))
        return True

    def put(self, request, *args, **kwargs):
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        success = False
        try:
            self.clean_password(request.user.email, current_password)
            self.clean_password2(request.user, current_password, new_password)
            request.user.set_password(new_password)
            request.user.save()
            obj = OldPasswords.objects.create(user=request.user)
            obj.setPasswords(request.user.password)
            obj.save()
            success = True
            response = {}
            status = 200
            return get_api_response(success, response, status)
        except ValidationError as e:
            response = {"message": e.message}
        if success:
            status = 200
        else:
            status = 400
        return get_api_response(success, response, status)
