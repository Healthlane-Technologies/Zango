from zelthy.core.generic_views.base import ZelthySessionPlatformTemplateView


class AppPanelView(ZelthySessionPlatformTemplateView):
    """
    View to render the App Panel accessible only to platform users.
    """

    template_name = "app_panel.html"
