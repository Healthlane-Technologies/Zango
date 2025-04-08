from django.urls import path, re_path
from .views import TestAPIView, TestView, TestPathParamView, TestREPathView, TestDataView

urlpatterns = [
    path("api/", TestAPIView.as_view(), name="customer"),
    path("view/", TestView.as_view(), name="dummy"),
    path("path/<str:param>/", TestPathParamView.as_view(), name="path_param"),
    re_path(r'^re_path/(?P<param>\w+)/$', TestREPathView.as_view(), name="re_path_param"),
    path("data/", TestDataView.as_view())
]
