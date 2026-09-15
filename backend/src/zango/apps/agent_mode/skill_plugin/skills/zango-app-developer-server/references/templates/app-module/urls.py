from django.urls import path, re_path
from .views import AppView, RedirectAppView

urlpatterns = [
    re_path(r'^app/', AppView.as_view()),
    re_path(r'^/', RedirectAppView.as_view()),
    re_path(r'^login/', RedirectAppView.as_view()),
]
