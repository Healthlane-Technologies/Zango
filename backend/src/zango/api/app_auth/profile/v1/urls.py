from django.urls import re_path

from .views import PasswordChangeViewAPIV1, ProfileViewAPIV1


urlpatterns = [
    re_path(
        r"change_password", PasswordChangeViewAPIV1.as_view(), name="change_password"
    ),
    re_path(r"", ProfileViewAPIV1.as_view(), name="profile"),
]
