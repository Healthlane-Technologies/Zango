from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from zelthy.core.api import get_api_response, ZelthyGenericAppAPIView, ZelthySessionAppAPIView
from zelthy.apps.appauth.login.utils import PasswordValidationMixin

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

    def clean_password(self, password):
        """
        Validates that the email is not already in use.
        """

        try:
            user = authenticate(
                username=self.user.email, password=self.cleaned_data["password"]
            )
        except:
            raise ValidationError("The current password you have entered is wrong. Please try again!")
        return True
    
    def clean_password2(self, password, password1):
        """method to validate password"""
        password2 = password1
        validation = self.run_all_validations(self.request.user, password1, password2, password)
        if not validation.get("validation"):
            raise ValidationError(validation.get("msg"))
        return True

    
    def put(self, request, *args, **kwargs):
        password = request.data.get("password")
        password1 = request.data.get("password1")
        if self.clean_password(password):
            if self.clean_password2(password, password1):
                request.user.set_password(password)
                request.user.save()
                obj = self.request.user.oldpassword_model.objects.create(user=request.user)
                obj.setPasswords(request.user.password)
                obj.save()
                success = True
                response = {}
                status = 200
                return get_api_response(success, response, status)
        if success:
            status = 200
        else:
            status = 400
        return get_api_response(success, response, status)