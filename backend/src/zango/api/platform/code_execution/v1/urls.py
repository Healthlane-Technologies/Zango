from django.urls import path

from .views import (
    CodeExecFileDownloadView,
    CodeExecFileListView,
    CodeExecutionAbortView,
    CodeExecutionDetailView,
    CodeExecutionExportView,
    CodeExecutionListView,
    CodeExecutionLogTailView,
    CodeSnippetArchiveView,
    CodeSnippetDetailView,
    CodeSnippetFileDeleteView,
    CodeSnippetFileDownloadView,
    CodeSnippetFileListView,
    CodeSnippetListView,
    CodeSnippetRunView,
    CodeSnippetUpdateView,
    CodeSnippetValidateView,
    CodeSnippetVersionsView,
)


# GET + POST only on the wire. Updates and deletes are POSTs to action paths.
urlpatterns = [
    # Snippets
    path("snippets/", CodeSnippetListView.as_view()),
    path("snippets/validate/", CodeSnippetValidateView.as_view()),
    path("snippets/<uuid:snippet_uuid>/", CodeSnippetDetailView.as_view()),
    path("snippets/<uuid:snippet_uuid>/update/", CodeSnippetUpdateView.as_view()),
    path("snippets/<uuid:snippet_uuid>/archive/", CodeSnippetArchiveView.as_view()),
    path("snippets/<uuid:snippet_uuid>/run/", CodeSnippetRunView.as_view()),
    path("snippets/<uuid:snippet_uuid>/versions/", CodeSnippetVersionsView.as_view()),
    # Snippet files
    path("snippets/<uuid:snippet_uuid>/files/", CodeSnippetFileListView.as_view()),
    path(
        "snippets/<uuid:snippet_uuid>/files/<uuid:file_uuid>/delete/",
        CodeSnippetFileDeleteView.as_view(),
    ),
    path(
        "snippets/<uuid:snippet_uuid>/files/<uuid:file_uuid>/download/",
        CodeSnippetFileDownloadView.as_view(),
    ),
    # Executions
    path("executions/", CodeExecutionListView.as_view()),
    path("executions/export.csv", CodeExecutionExportView.as_view()),
    path("executions/<uuid:execution_uuid>/", CodeExecutionDetailView.as_view()),
    path(
        "executions/<uuid:execution_uuid>/log-tail/",
        CodeExecutionLogTailView.as_view(),
    ),
    path(
        "executions/<uuid:execution_uuid>/abort/",
        CodeExecutionAbortView.as_view(),
    ),
    # Execution files
    path(
        "executions/<uuid:execution_uuid>/files/",
        CodeExecFileListView.as_view(),
    ),
    path(
        "executions/<uuid:execution_uuid>/files/<uuid:file_uuid>/download/",
        CodeExecFileDownloadView.as_view(),
    ),
]
