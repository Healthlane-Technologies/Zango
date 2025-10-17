from django.urls import re_path

from .views import ProfileViewAPIV1


urlpatterns = [
    re_path(r"", ProfileViewAPIV1.as_view(), name="profile"),
]
