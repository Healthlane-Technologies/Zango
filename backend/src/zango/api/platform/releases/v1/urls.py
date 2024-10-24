from django.urls import path

from .views import AppReleaseView


urlpatterns = [
    path("", AppReleaseView.as_view()),
]
