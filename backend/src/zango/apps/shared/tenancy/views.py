from celery import current_app

from zango.core.api import (
    ZangoGenericPlatformAPIView,
    get_api_response,
)
from zango.core.generic_views.base import ZangoSessionPlatformTemplateView


class AppPanelView(ZangoSessionPlatformTemplateView):
    """
    View to render the App Panel accessible only to platform users.
    """

    template_name = "app_panel.html"

    def get_context_data(self, **kwargs):
        import zango

        context = super().get_context_data(**kwargs)
        context["platform_version"] = zango.__version__
        return context


class CeleryStatusAPIView(ZangoGenericPlatformAPIView):
    def get(self, request, *args, **kwargs):
        try:
            # Inspect the active workers
            i = current_app.control.inspect()
            active_workers = i.ping()

            is_running = bool(active_workers)  # True if there are active workers

            response = {
                "status": is_running,
                "active_workers": active_workers or {},
            }
            success = True
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)
