from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, View

from ..permissions import IsAuthenticatedAppUser, IsAuthenticatedPlatformUser


class ZangoSessionPlatformView(IsAuthenticatedPlatformUser, View):
    """
    View only accessible to authenticated platform users.
    """

    @classmethod
    def as_view(cls):
        login_url = None
        return login_required(
            super(ZangoSessionPlatformView, cls).as_view(), login_url=login_url
        )


class ZangoSessionPlatformTemplateView(IsAuthenticatedPlatformUser, TemplateView):
    """
    TemplateView only accessible to authenticated platform users.
    """

    @classmethod
    def as_view(cls):
        login_url = "/auth/login/"
        return login_required(
            super(ZangoSessionPlatformTemplateView, cls).as_view(), login_url=login_url
        )


class ZangoSessionAppView(IsAuthenticatedAppUser, View):
    """
    View only accessible to authenticated app users.
    """

    @classmethod
    def as_view(cls):
        login_url = None
        return login_required(
            super(ZangoSessionAppView, cls).as_view(), login_url=login_url
        )


class ZangoSessionAppTemplateView(IsAuthenticatedAppUser, TemplateView):
    """
    TemplateView only accessible to authenticated app users.
    """

    @classmethod
    def as_view(cls):
        login_url = None
        return login_required(
            super(ZangoSessionAppTemplateView, cls).as_view(), login_url=login_url
        )
