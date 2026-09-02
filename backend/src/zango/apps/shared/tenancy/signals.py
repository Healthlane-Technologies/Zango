from corsheaders.signals import check_request_enabled

from django.dispatch import receiver


def _build_origins(domains):
    """
    Expand tenant hostnames into the origin strings a browser sends in the
    Origin header.
    """
    return {f"https://{domain}" for domain in domains}


def _tenant_origins(request):
    """
    Origins belonging to the tenant that is serving this request.

    Returns an empty set on the public schema (platform panel, health checks)
    so that CORS_ALLOWED_ORIGINS alone decides those.

    The result is memoised on the request rather than in the shared cache:
    CorsMiddleware may consult the signal more than once per request, but a
    cross-process cache would put a network call on the path of every
    cross-origin request, and an unreachable cache backend would then stall or
    break CORS for everyone. One indexed lookup on a small table is cheaper
    than that risk, and the tenant row has already been fetched by
    ZangoTenantMainMiddleware moments earlier.
    """
    tenant = getattr(request, "tenant", None)
    if not tenant:
        return set()

    origins = getattr(request, "_cors_tenant_origins", None)
    if origins is None:
        origins = _build_origins(tenant.domains.values_list("domain", flat=True))
        request._cors_tenant_origins = origins
    return origins


@receiver(check_request_enabled)
def cors_allow_tenant_domains(sender, request, **kwargs):
    """
    Allow a cross-origin request when the Origin is one of the requesting
    tenant's own registered domains.

    Returning False does not veto the request: django-cors-headers ORs this
    receiver with CORS_ALLOWED_ORIGINS and CORS_ALLOWED_ORIGIN_REGEXES, so the
    static allow-list is still honoured for platform and embed origins.
    """
    origin = request.headers.get("Origin", "")
    return bool(origin) and origin in _tenant_origins(request)
