from django.urls import path

from .views import TemplateDetailView, TemplateListView


urlpatterns = [
    path("templates/", TemplateListView.as_view()),
    path("templates/<slug:slug>/", TemplateDetailView.as_view()),
]
