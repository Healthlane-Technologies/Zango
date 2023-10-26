from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from knox.auth import TokenAuthentication

from ..permissions import IsAuthenticatedPlatformUser, IsAuthenticatedAppUser



class ZelthySessionPlatformAPIView(APIView):
    """
    This is the base class for developing Platform APIs that need to support only session based
    authentication. Expected use cases include APIs that must be supported only with session and NOT token
    """

    authentication_classes = (SessionAuthentication, )
    permission_classes = (IsAuthenticatedPlatformUser,)
    

class ZelthySessionAppAPIView(APIView):
    """
    Base API view for developing Session Authenticated Platform APIs
    Use Case: Platform APIs accessed by the web apps on the same domain
    CSRF Not Exempted
    This API expects zelthycookie & csrftoken as Cookies. zelthycookie should 
    represent an active platform user.
    Additional Perms: Request should pass whitelisting setting of Platform
    """

    authentication_classes = (SessionAuthentication, )
    permission_classes = (IsAuthenticatedAppUser,)



class ZelthyTokenPlatformAPIView(APIView):
    """
    This is the base class for developing Platform APIs that need to support only token based
    authentication. Expected use cases include APIs that will be used by third parties only
    """

    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticatedPlatformUser,)




class ZelthyGenericPlatformAPIView(APIView):
    """
    This is the base auth class for developing Platform APIs that need to support both
    token based authentication as well as session cookie based authentication.
    The Zelthy platform webapp must use session based authentication and should provide csrftoken as well.
    """

    authentication_classes = (SessionAuthentication,
                                TokenAuthentication)
    permission_classes = (IsAuthenticatedPlatformUser,)

class ZelthyGenericAppAPIView(APIView):

    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticatedAppUser,)