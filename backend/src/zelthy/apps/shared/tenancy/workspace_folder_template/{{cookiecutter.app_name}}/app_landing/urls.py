from django.urls import path
from .views import AppLandingPageView

urlpatterns = [
    path("app/home/", AppLandingPageView.as_view()),
]
