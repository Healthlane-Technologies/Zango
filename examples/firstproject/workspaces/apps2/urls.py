from django.urls import re_path, include
from zelthy.core.urls import z_include


urlpatterns = [
    re_path(r'^mod1/', include('module1.urls')),
    # re_path(r'^mod2/', z_include('module2.urls')),
    # re_path(r'^frame/', z_include('frame.urls')),
]