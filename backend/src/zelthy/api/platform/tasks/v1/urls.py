from django.urls import path, re_path
from .views import AppTaskView, AppTaskDetailView

urlpatterns = [
    path("", AppTaskView.as_view()),
    re_path(r"(?P<task_uuid>[\w-]+)/", AppTaskDetailView.as_view()),
]
