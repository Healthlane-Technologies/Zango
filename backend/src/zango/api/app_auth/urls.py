from django.urls import include, path

from .config.v1 import urls as config_v1_urls
from .flows.v1 import urls as flows_v1_urls
from .profile.v1 import urls as profile_v1_urls


urlpatterns = [
    path("v1/profile/", include(profile_v1_urls)),
    path("v1/appauth/config/", include(config_v1_urls)),
    path("v1/appauth/", include(flows_v1_urls)),
]
