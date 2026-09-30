from django.urls import path

from .views import (
    TemplateBuilderPageView,
    TemplateBuilderView,
    TemplateDetailView,
    TemplateListView,
)


urlpatterns = [
    path("templates/", TemplateListView.as_view()),
    path("templates/<slug:slug>/", TemplateDetailView.as_view()),
    path(
        "templates/<slug:slug>/versions/<uuid:version_uuid>/builder/",
        TemplateBuilderView.as_view(),
    ),
    path(
        "templates/<slug:slug>/versions/<uuid:version_uuid>/builder.html",
        TemplateBuilderPageView.as_view(),
    ),
]
