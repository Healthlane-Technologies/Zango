from zelthy.core.generic_views.base import (
    ZelthySessionAppTemplateView,
)
from django.views.generic import View


class AppLandingPageView(ZelthySessionAppTemplateView):
    template_name = "app_landing.html"

    def get(self, request, *args, **kwargs):
        return super(AppLandingPageView, self).get(request, *args, **kwargs)
