from django.urls import re_path

from .views import ConversationViewAPIV1


urlpatterns = [
    re_path(
        r"^conversation/$",
        ConversationViewAPIV1.as_view(),
        name="codeassit-apiv1-conversation",
    ),
]
