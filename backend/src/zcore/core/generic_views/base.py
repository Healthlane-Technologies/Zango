from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from ..permissions import IsAuthenticatedPlatformUser, IsAuthenticatedAppUser


class ZelthySessionPlatformView(IsAuthenticatedPlatformUser, View):
    """
    View only accessible to authenticated platform users.
    """

    @classmethod
    def as_view(cls):
        login_url = None
        return login_required(
            super(ZelthySessionPlatformView, cls).as_view(), login_url=login_url
        )


class ZelthySessionPlatformTemplateView(IsAuthenticatedPlatformUser, TemplateView):
    """
    TemplateView only accessible to authenticated platform users.
    """

    @classmethod
    def as_view(cls):
        login_url = "/admin/login/"
        return login_required(
            super(ZelthySessionPlatformTemplateView, cls).as_view(), login_url=login_url
        )


class ZelthySessionAppView(IsAuthenticatedAppUser, View):
    """
    View only accessible to authenticated app users.
    """

    @classmethod
    def as_view(cls):
        login_url = None
        return login_required(
            super(ZelthySessionAppView, cls).as_view(), login_url=login_url
        )

class ZelthySessionAppTemplateView(IsAuthenticatedAppUser, TemplateView):
    """
    TemplateView only accessible to authenticated app users.
    """

    @classmethod
    def as_view(cls):
        login_url = None
        return login_required(
            super(ZelthySessionAppTemplateView, cls).as_view(), login_url=login_url
        )
