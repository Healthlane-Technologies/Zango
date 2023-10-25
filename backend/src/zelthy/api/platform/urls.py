from django.urls import path, include

from .tenancy.v1 import urls as tenancy_v1_urls
from .auth.v1 import urls as auth_v1_urls
from .packages.v1 import urls as packages_v1_urls

urlpatterns = [
    path("v1/apps/", include(tenancy_v1_urls)),
    path("v1/auth/", include(auth_v1_urls)),
]
