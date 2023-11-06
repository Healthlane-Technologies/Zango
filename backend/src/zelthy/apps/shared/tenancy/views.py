import os
from zelthy.core.generic_views.base import ZelthySessionPlatformTemplateView
from zelthy.apps.permissions.models import PolicyModel
from zelthy.apps.appauth.models import AppUserModel, UserRoleModel


class AppPanelView(ZelthySessionPlatformTemplateView):
    """
    View to render the App Panel accessible only to platform users.
    """

    template_name = "app_panel.html"
