from importlib import import_module

from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpRequest, SimpleCookie
from django.test import Client, RequestFactory

from zango.core.utils import get_mock_request
from zango.middleware.tenant import ZangoTenantMainMiddleware


class BaseZangoRequestFactory:
    tm = ZangoTenantMainMiddleware(lambda r: r)

    def __init__(self, tenant, **defaults):
        super().__init__(**defaults)
        self.tenant = tenant
        self.user = None

    def generic(self, *args, **kwargs):
        if "HTTP_HOST" not in kwargs:
            kwargs["HTTP_HOST"] = self.tenant.get_primary_domain().domain
        request = super().generic(*args, **kwargs)
        # Assign the tenant to the request object
        request.tenant = self.tenant
        if request.tenant.tenant_type == "app":
            request.user = self.user
        return request


class ZangoRequestFactory(BaseZangoRequestFactory, RequestFactory):
    pass


class ZangoClient(ZangoRequestFactory, Client):
    def logout(self):
        """Log out the user by removing the cookies and session object."""
        from django.contrib.auth import logout

        request = HttpRequest()
        request.user = None
        if self.session:
            request.session = self.session
            request.user = self.user
        else:
            engine = import_module(settings.SESSION_ENGINE)
            request.session = engine.SessionStore()
        logout(request)
        self.cookies = SimpleCookie()

    def _login(self, user, backend=None):
        from django.contrib.auth import login

        request = get_mock_request(session=self.session)
        login(request, user, backend)
        request.session.save()

        # Set the session cookie in the client.
        session_cookie = settings.SESSION_COOKIE_NAME
        self.cookies[session_cookie] = request.session.session_key
        self.cookies[session_cookie].update(
            {
                "max-age": None,
                "path": "/",
                "domain": settings.SESSION_COOKIE_DOMAIN,
                "secure": settings.SESSION_COOKIE_SECURE or None,
                "expires": None,
            }
        )

    def login(self, **credentials):
        request = get_mock_request(session=self.session)
        user = authenticate(request, **credentials)

        if user:
            self._login(user)
            return True

        return False
