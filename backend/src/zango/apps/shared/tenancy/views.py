import os
from zango.core.generic_views.base import ZangoSessionPlatformTemplateView
from zango.apps.permissions.models import PolicyModel
from zango.apps.appauth.models import AppUserModel, UserRoleModel


class AppPanelView(ZangoSessionPlatformTemplateView):
    """
    View to render the App Panel accessible only to platform users.
    """

    template_name = "app_panel.html"
