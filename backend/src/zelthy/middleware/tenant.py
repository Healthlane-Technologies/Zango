import pytz

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.db import connection
from django.http import Http404
from django.urls import set_urlconf
from django.utils.deprecation import MiddlewareMixin
from django_tenants.utils import (
    remove_www,
    get_public_schema_name,
    get_tenant_types,
    has_multi_type_tenants,
    get_tenant_domain_model,
    get_public_schema_urlconf,
)
from django_tenants.middleware.main import TenantMainMiddleware
from django.conf import settings
from django.utils import timezone


class ZelthyTenantMainMiddleware(TenantMainMiddleware):
    TENANT_NOT_FOUND_EXCEPTION = Http404

    @staticmethod
    def hostname_from_request(request):
        """
        Static method to extract hostname from request.

        Args:
            request: The request object.

        Returns:
            The hostname extracted from the request.
        """
        return remove_www(request.get_host().split(":")[0])

    def get_tenant(self, domain_model, hostname):
        """
        Get the tenant associated with the given domain and hostname.

        Args:
            domain_model: The domain model class.
            hostname: The hostname for which to retrieve the tenant.

        Returns:
            The tenant associated with the given domain and hostname.
        """
        domain = domain_model.objects.select_related("tenant").get(domain=hostname)
        return domain.tenant

    def __call__(self, request):
        """
        Determines the tenant based on the request's hostname,
        setting the tenant's domain URL, and configuring the database connection to use the
        tenant's schema. It also handles routing and sets up URL routing based on the tenant
        """
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

        return self.get_response(request)

    def no_tenant_found(self, request, hostname):
        """
        Handle the case when no tenant is found for a given hostname.

        Args:
            self: The instance of the class.
            request: The request object.
            hostname: The hostname for which the tenant is not found.

        Raises:
            TENANT_NOT_FOUND_EXCEPTION: If no tenant is found for the given hostname.

        Returns:
            None
        """
        if (
            hasattr(settings, "SHOW_PUBLIC_IF_NO_TENANT_FOUND")
            and settings.SHOW_PUBLIC_IF_NO_TENANT_FOUND
        ):
            self.setup_url_routing(request=request, force_public=True)
        else:
            raise self.TENANT_NOT_FOUND_EXCEPTION(
                'No tenant for hostname "%s"' % hostname
            )

    @staticmethod
    def setup_url_routing(request, force_public=False):
        """
        Set up URL routing based on the provided request
        and optionally enforce public schema routing.

        Args:
            request: The request object.
            force_public (bool): Flag to force public URL routing.

        Returns:
            None
        """
        public_schema_name = get_public_schema_name()
        if has_multi_type_tenants():
            tenant_types = get_tenant_types()
            if not hasattr(request, "tenant") or (
                (force_public or request.tenant.schema_name == get_public_schema_name())
                and "URLCONF" in tenant_types[public_schema_name]
            ):
                request.urlconf = get_public_schema_urlconf()
            else:
                tenant_type = request.tenant.get_tenant_type()
                request.urlconf = tenant_types[tenant_type]["URLCONF"]
            set_urlconf(request.urlconf)

        else:
            # Do we have a public-specific urlconf?
            if hasattr(settings, "PUBLIC_SCHEMA_URLCONF") and (
                force_public or request.tenant.schema_name == get_public_schema_name()
            ):
                request.urlconf = settings.PUBLIC_SCHEMA_URLCONF


class TimezoneMiddleware(MiddlewareMixin):
    def __call__(self, request):
        """
        Sets the timezone for the request based on the tenant's timezone.
        It then sets the default region for phone_numbers based on the timezone_country mapping.
        If timezone is not set, timezone is deactivated.
        """
        try:
            tzname = request.tenant.timezone
            timezone.activate(pytz.timezone(tzname))
            timezone_country = {}
            for countrycode in pytz.country_timezones:
                timezones = pytz.country_timezones[countrycode]
                for tz in timezones:
                    timezone_country[tz] = countrycode
            settings.PHONENUMBER_DEFAULT_REGION = timezone_country[tzname]
        except Exception as e:
            timezone.deactivate()
        return self.get_response(request)
