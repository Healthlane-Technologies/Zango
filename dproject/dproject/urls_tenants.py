from django.contrib import admin
from django.urls import path, include, re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('zelthy.config.urls_tenants')),
    re_path('mod1/', include("loadtest_0.urls")),
    re_path('mod1/', include("loadtest_1.urls")),
    re_path('mod1/', include("loadtest_2.urls")),
    re_path('mod1/', include("loadtest_3.urls")),
]
