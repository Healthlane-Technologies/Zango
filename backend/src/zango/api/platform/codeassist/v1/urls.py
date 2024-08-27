from django.urls import re_path

from .views import ConversationViewAPIV1, ExecutionViewAPIV1


urlpatterns = [
    re_path(
        r"^conversation/$",
        ConversationViewAPIV1.as_view(),
        name="codeassit-apiv1-conversation",
    ),
    re_path(
        r"^execute/$",
        ExecutionViewAPIV1.as_view(),
        name="codeassit-apiv1-execute",
    ),
]
