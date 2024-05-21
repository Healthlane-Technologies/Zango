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
