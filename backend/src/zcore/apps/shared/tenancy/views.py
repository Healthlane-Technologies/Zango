import os
from zcore.core.generic_views.base import ZelthySessionPlatformTemplateView
from zcore.apps.permissions.models import PolicyModel
from zcore.apps.appauth.models import AppUserModel, UserRoleModel


class AppPanelView(ZelthySessionPlatformTemplateView):
    """
    View to render the App Panel accessible only to platform users.
    """

    template_name = "app_panel.html"
