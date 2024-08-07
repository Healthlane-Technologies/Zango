from django.test import RequestFactory, Client
from zango.middleware.tenant import ZangoTenantMainMiddleware
from django.contrib.auth import authenticate
from zango.core.utils import get_current_request
class BaseZangoRequestFactory:
    tm = ZangoTenantMainMiddleware(lambda r: r)

    def __init__(self, tenant, **defaults):
        super().__init__(**defaults)
        self.tenant = tenant

    def generic(self, *args, **kwargs):
        if "HTTP_HOST" not in kwargs:
            kwargs["HTTP_HOST"] = self.tenant.get_primary_domain().domain
        request = super().generic(*args, **kwargs)
        # Assign the tenant to the request object
        request.tenant = self.tenant
        return request
    
class ZangoRequestFactory(BaseZangoRequestFactory, RequestFactory):
    pass


class ZangoClient(BaseZangoRequestFactory, Client):
    def login(self, **credentials):
        request = get_current_request()
        user = authenticate(request, **credentials)
        if user:
            # super(ZangoClient, self)._login(user)
            return True
        else:
            return False