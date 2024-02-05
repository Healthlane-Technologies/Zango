import pytz

from django.conf import settings
from django.utils import timezone
from django.core.exceptions import DisallowedHost
from django.db import connection
from django.http import Http404
from django.urls import set_urlconf
from django.utils.deprecation import MiddlewareMixin

from django_tenants.utils import remove_www, get_public_schema_name, get_tenant_types, \
    has_multi_type_tenants, get_tenant_domain_model, get_public_schema_urlconf

from django_tenants.middleware.main import TenantMainMiddleware

from collections import OrderedDict
from django.apps import apps
from django.conf import settings
from django.core import management



class ZelthyTenantMainMiddleware(TenantMainMiddleware):
    TENANT_NOT_FOUND_EXCEPTION = Http404
    """
    This middleware should be placed at the very top of the middleware stack.
    Selects the proper database schema using the request host. Can fail in
    various ways which is better than corrupting or revealing data.
    """

    @staticmethod
    def hostname_from_request(request):
        """ Extracts hostname from request. Used for custom requests filtering.
            By default removes the request's port and common prefixes.
        """
        return remove_www(request.get_host().split(':')[0])

    def get_tenant(self, domain_model, hostname):
        domain = domain_model.objects.select_related('tenant').get(domain=hostname)
        return domain.tenant

    def process_request(self, request):
        # Connection needs first to be at the public schema, as this is where
        # the tenant metadata is stored.
        
        connection.set_schema_to_public()
        try:
            hostname = self.hostname_from_request(request)
        except DisallowedHost:
            from django.http import HttpResponseNotFound
            return HttpResponseNotFound()
        domain_model = get_tenant_domain_model()
        try:
            tenant = self.get_tenant(domain_model, hostname)
        except domain_model.DoesNotExist:
            self.no_tenant_found(request, hostname)
            return

        tenant.domain_url = hostname
        request.tenant = tenant
        request.internal_routing = False
        connection.set_tenant(request.tenant)
        self.setup_url_routing(request)
        # sa_base.base = declarative_base()
        # new_app_name = "zelthy_apps.Tenant3"

        # settings.INSTALLED_APPS += (new_app_name, )
        # apps.app_configs = OrderedDict()
        # apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
        # apps.clear_cache()
        # apps.populate(settings.INSTALLED_APPS)


    def no_tenant_found(self, request, hostname):
        """ What should happen if no tenant is found.
        This makes it easier if you want to override the default behavior """
        if hasattr(settings, 'SHOW_PUBLIC_IF_NO_TENANT_FOUND') and settings.SHOW_PUBLIC_IF_NO_TENANT_FOUND:
            self.setup_url_routing(request=request, force_public=True)
        else:
            raise self.TENANT_NOT_FOUND_EXCEPTION('No tenant for hostname "%s"' % hostname)

    @staticmethod
    def setup_url_routing(request, force_public=False):
        """
        Sets the correct url conf based on the tenant
        :param request:
        :param force_public
        """
        public_schema_name = get_public_schema_name()
        if has_multi_type_tenants():
            tenant_types = get_tenant_types()
            if (not hasattr(request, 'tenant') or
                    ((force_public or request.tenant.schema_name == get_public_schema_name()) and
                     'URLCONF' in tenant_types[public_schema_name])):
                request.urlconf = get_public_schema_urlconf()
            else:
                tenant_type = request.tenant.get_tenant_type()
                request.urlconf = tenant_types[tenant_type]['URLCONF']
            set_urlconf(request.urlconf)

        else:
            # Do we have a public-specific urlconf?
            if (hasattr(settings, 'PUBLIC_SCHEMA_URLCONF') and
                    (force_public or request.tenant.schema_name == get_public_schema_name())):
                request.urlconf = settings.PUBLIC_SCHEMA_URLCONF

class TimezoneMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            tzname = request.tenant.timezone
            timezone.activate(pytz.timezone(tzname))
            australian_timezones = ['Australia/ACT', 'Australia/Adelaide', 'Australia/Brisbane',
                                    'Australia/Broken_Hill', 'Australia/Canberra', 'Australia/Currie',
                                    'Australia/Darwin', 'Australia/Eucla', 'Australia/Hobart',
                                    'Australia/LHI', 'Australia/Lindeman', 'Australia/Lord_Howe',
                                    'Australia/Melbourne', 'Australia/NSW', 'Australia/North',
                                    'Australia/Perth', 'Australia/Queensland', 'Australia/South',
                                    'Australia/Sydney', 'Australia/Tasmania', 'Australia/Victoria',
                                    'Australia/West', 'Australia/Yancowinna']

            if tzname == 'Asia/Bangkok':    
                settings.PHONENUMBER_DEFAULT_REGION = 'TH'  
            elif tzname == 'Asia/Kolkata':  
                settings.PHONENUMBER_DEFAULT_REGION = 'IN'  
            elif tzname == 'Asia/Singapore':    
                settings.PHONENUMBER_DEFAULT_REGION = 'SG'  
            elif tzname == 'Asia/Taipei':   
                settings.PHONENUMBER_DEFAULT_REGION = 'TW'  
            elif tzname == 'Asia/Hong_Kong':    
                settings.PHONENUMBER_DEFAULT_REGION = 'HK'  
            elif tzname == 'Asia/Kuala_Lumpur': 
                settings.PHONENUMBER_DEFAULT_REGION = 'MY'  
            elif tzname == 'Asia/Ho_Chi_Minh':  
                settings.PHONENUMBER_DEFAULT_REGION = 'VN'
            elif tzname in australian_timezones:
                settings.PHONENUMBER_DEFAULT_REGION = 'AU'
            elif tzname == 'Pacific/Auckland':
                settings.PHONENUMBER_DEFAULT_REGION = 'NZ'
                
        except:
            timezone.deactivate()