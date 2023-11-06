import os
from zelthy.core.generic_views.base import ZelthySessionPlatformTemplateView
from zelthy.apps.permissions.models import PolicyModel
from zelthy.apps.appauth.models import AppUserModel, UserRoleModel


class DynamicPanelView(ZelthySessionPlatformTemplateView):
    """
    View to render the Dynamic Panel accessible only to platform users.
    """

    template_name = "dynamic_panel.html"
