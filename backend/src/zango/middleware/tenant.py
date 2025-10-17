import pytz

from django_tenants.middleware.main import TenantMainMiddleware
from django_tenants.utils import (
    get_public_schema_name,
    get_public_schema_urlconf,
    get_tenant_domain_model,
    get_tenant_model,
    get_tenant_types,
    has_multi_type_tenants,
    remove_www,
)

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.db import connection
from django.http import Http404
from django.urls import set_urlconf
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from zango.core.utils import get_region_from_timezone


class ZangoTenantMainMiddleware(TenantMainMiddleware):
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

    def get_public_tenant(self):
        """
        Retrieve the public tenant.

        This method fetches the tenant that is marked as "shared" in the tenant model.

        Returns:
            Tenant: The tenant instance with `tenant_type="shared"`.

        Raises:
            DoesNotExist: If no tenant with `tenant_type="shared"` exists.
            MultipleObjectsReturned: If multiple tenants with `tenant_type="shared"` exist.
        """
        tenant_model = get_tenant_model()
        tenant = tenant_model.objects.get(tenant_type="shared")
        return tenant

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
            if request.path == "/api/v1/health/":
                tenant = self.get_public_tenant()
                hostname = tenant.get_primary_domain().domain
            else:
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
        Sets the timezone for the request based on the X-Client-Timezone header first,
        falling back to the tenant's timezone.
        It then sets the default region for phone_numbers based on the timezone_country mapping.
        If timezone is not set, timezone is deactivated.
        """
        try:
            # Priority 1: X-Client-Timezone header
            tzname = request.headers.get("X-Client-Timezone")

            # Priority 2: Tenant's timezone
            if not tzname:
                tzname = request.tenant.timezone

            if tzname:
                request.tzname = tzname
                timezone.activate(pytz.timezone(tzname))
            else:
                request.tzname = None
                timezone.deactivate()
        except Exception:
            request.tzname = None
            timezone.deactivate()

        # Set default region for phone number
        phonenumber_region = None
        try:
            # Always use tenant timezone for phone number region
            if request.tenant.timezone:
                phonenumber_region = get_region_from_timezone(request.tenant.timezone)
        except Exception:
            phonenumber_region = None

        if phonenumber_region:
            settings.PHONENUMBER_DEFAULT_REGION = phonenumber_region

        return self.get_response(request)
