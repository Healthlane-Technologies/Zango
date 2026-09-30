from django.urls import re_path

from .views import ConsoleView


urlpatterns = [
    re_path(r"^", ConsoleView.as_view(), name="console"),
]
