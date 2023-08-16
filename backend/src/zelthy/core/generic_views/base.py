
from django.views.generic import View, TemplateView
from django.contrib.auth.decorators import login_required
from ..permissions import IsAuthenticatedPlatformUser

class ZelthySessionPlatformView(IsAuthenticatedPlatformUser, View):
    """

    """
    @classmethod
    def as_view(cls):
        login_url = None
        return login_required(
                super(ZelthySessionPlatformView, cls
                ).as_view(), login_url=login_url)




class ZelthySessionPlatformTemplateView(
                        IsAuthenticatedPlatformUser, TemplateView):
    """

    """
    @classmethod
    def as_view(cls):
        login_url = None
        return login_required(
                super(ZelthySessionPlatformTemplateView, cls
                ).as_view(), login_url=login_url)


    