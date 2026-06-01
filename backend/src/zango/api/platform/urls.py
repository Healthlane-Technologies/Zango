from django.urls import include, path

from .auth.v1 import urls as auth_v1_urls
from .code_execution.v1 import urls as code_execution_v1_urls
from .codebase.v1 import urls as codebase_v1_urls
from .platform_logs.v1.urls import admin_urls as platform_logs_admin_urls
from .platform_logs.v1.urls import in_app_urls as platform_logs_in_app_urls
from .tenancy.v1 import urls as tenancy_v1_urls


urlpatterns = [
    path("v1/apps/", include(tenancy_v1_urls)),
    path("v1/auth/", include(auth_v1_urls)),
    path("v1/apps/<uuid:app_uuid>/codebase/", include(codebase_v1_urls)),
    path(
        "v1/apps/<uuid:app_uuid>/code-execution/",
        include(code_execution_v1_urls),
    ),
    path("v1/apps/<uuid:app_uuid>/logs/", include(platform_logs_in_app_urls)),
    path("v1/platform/logs/", include(platform_logs_admin_urls)),
]
