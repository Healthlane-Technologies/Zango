from django.urls import re_path

from .views import AppPanelView
from zango.core.decorators import internal_access_only

urlpatterns = [
    re_path(r"^", internal_access_only(AppPanelView.as_view()), name="platform")
]
