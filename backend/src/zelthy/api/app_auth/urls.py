from django.urls import path, include

from .profile.v1 import urls as profile_v1_urls

urlpatterns = [
    path("v1/profile/", include(profile_v1_urls)),
]