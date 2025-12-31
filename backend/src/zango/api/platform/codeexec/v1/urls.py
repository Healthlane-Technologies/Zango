from django.urls import path

from .views import CodeExecExecuteViewAPIV1, CodeExecViewAPIV1


urlpatterns = [
    path("", CodeExecViewAPIV1.as_view()),
    path("execute/", CodeExecExecuteViewAPIV1.as_view()),
]
