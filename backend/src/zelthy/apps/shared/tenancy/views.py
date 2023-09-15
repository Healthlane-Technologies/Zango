from zelthy.core.generic_views.base import ZelthySessionPlatformTemplateView


class DynamicPanelView(ZelthySessionPlatformTemplateView):
    """
    View to render the Dynamic Panel accessible only to platform users.
    """

    template_name = "dynamic_panel.html"
