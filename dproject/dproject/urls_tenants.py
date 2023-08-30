from django.urls import path, include, re_path

urlpatterns = [
    re_path('mod1/', include('loadtest_0.urls')),
]
