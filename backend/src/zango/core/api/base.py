from knox.auth import TokenAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from zango.apps.appauth.auth_backend import KnoxTokenAuthBackend

from ..permissions import IsAuthenticatedAppUser, IsAuthenticatedPlatformUser


class ZangoSessionPlatformAPIView(APIView):
    """
    This is the base class for developing Platform APIs that need to support only session based
    authentication. Expected use cases include APIs that must be supported only with session and NOT token
    """

    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticatedPlatformUser,)


class ZangoSessionAppAPIView(APIView):
    """
    Base API view for developing Session Authenticated Platform APIs
    Use Case: Platform APIs accessed by the web apps on the same domain
    CSRF Not Exempted
    This API expects zangocookie & csrftoken as Cookies. zangocookie should
    represent an active platform user.
    Additional Perms: Request should pass whitelisting setting of Platform
    """

    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticatedAppUser,)


class ZangoTokenPlatformAPIView(APIView):
    """
    This is the base class for developing Platform APIs that need to support only token based
    authentication. Expected use cases include APIs that will be used by third parties only
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticatedPlatformUser,)


class ZangoGenericPlatformAPIView(APIView):
    """
    This is the base auth class for developing Platform APIs that need to support both
    token based authentication as well as session cookie based authentication.
    The Zango platform webapp must use session based authentication and should provide csrftoken as well.
    """

    authentication_classes = (SessionAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticatedPlatformUser, IsAuthenticated)


class ZangoGenericAppAPIView(APIView):
    authentication_classes = (
        SessionAuthentication,
        KnoxTokenAuthBackend,
    )
    permission_classes = (IsAuthenticated,)
