from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from ..permissions import IsAuthenticatedPlatformUser, IsAuthenticatedAppUser


class ZCoreSessionPlatformView(IsAuthenticatedPlatformUser, View):
    """
    View only accessible to authenticated platform users.
    """

    @classmethod
    def as_view(cls):
        login_url = None
        return login_required(
            super(ZCoreSessionPlatformView, cls).as_view(), login_url=login_url
        )


class ZCoreSessionPlatformTemplateView(IsAuthenticatedPlatformUser, TemplateView):
    """
    TemplateView only accessible to authenticated platform users.
    """

    @classmethod
    def as_view(cls):
        login_url = "/auth/login/"
        return login_required(
            super(ZCoreSessionPlatformTemplateView, cls).as_view(), login_url=login_url
        )


class ZCoreSessionAppView(IsAuthenticatedAppUser, View):
    """
    View only accessible to authenticated app users.
    """

    @classmethod
    def as_view(cls):
        login_url = None
        return login_required(
            super(ZCoreSessionAppView, cls).as_view(), login_url=login_url
        )

class ZCoreSessionAppTemplateView(IsAuthenticatedAppUser, TemplateView):
    """
    TemplateView only accessible to authenticated app users.
    """

    @classmethod
    def as_view(cls):
        login_url = None
        return login_required(
            super(ZCoreSessionAppTemplateView, cls).as_view(), login_url=login_url
        )
