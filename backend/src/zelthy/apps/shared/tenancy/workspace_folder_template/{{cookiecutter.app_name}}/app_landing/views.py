from zelthy.core.generic_views.base import (
    ZelthySessionAppTemplateView,
)
from django.views.generic import View

from ..plugins.frame.decorator import apply_frame_routing


class AppLandingPageView(ZelthySessionAppTemplateView):
    template_name = "app_landing.html"

    @apply_frame_routing
    def get(self, request, *args, **kwargs):
        return super(AppLandingPageView, self).get(request, *args, **kwargs)