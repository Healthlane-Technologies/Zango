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
)


# GET + POST only on the wire. Updates and deletes are POSTs to action paths.
urlpatterns = [
    # Snippets
    path("snippets/", CodeSnippetListView.as_view()),
    path("snippets/validate/", CodeSnippetValidateView.as_view()),
    path("snippets/<uuid:snippet_id>/", CodeSnippetDetailView.as_view()),
    path("snippets/<uuid:snippet_id>/update/", CodeSnippetUpdateView.as_view()),
    path("snippets/<uuid:snippet_id>/archive/", CodeSnippetArchiveView.as_view()),
    path("snippets/<uuid:snippet_id>/run/", CodeSnippetRunView.as_view()),
    # Snippet files
    path("snippets/<uuid:snippet_id>/files/", CodeSnippetFileListView.as_view()),
    path(
        "snippets/<uuid:snippet_id>/files/<uuid:file_id>/delete/",
        CodeSnippetFileDeleteView.as_view(),
    ),
    path(
        "snippets/<uuid:snippet_id>/files/<uuid:file_id>/download/",
        CodeSnippetFileDownloadView.as_view(),
    ),
    # Executions
    path("executions/", CodeExecutionListView.as_view()),
    path("executions/export.csv", CodeExecutionExportView.as_view()),
    path("executions/<uuid:execution_id>/", CodeExecutionDetailView.as_view()),
    path(
        "executions/<uuid:execution_id>/log-tail/",
        CodeExecutionLogTailView.as_view(),
    ),
    path(
        "executions/<uuid:execution_id>/abort/",
        CodeExecutionAbortView.as_view(),
    ),
    # Execution files
    path(
        "executions/<uuid:execution_id>/files/",
        CodeExecFileListView.as_view(),
    ),
    path(
        "executions/<uuid:execution_id>/files/<uuid:file_id>/download/",
        CodeExecFileDownloadView.as_view(),
    ),
]
