import ipaddress

from ipware.ip import get_client_ip

from django.conf import settings
from django.core.exceptions import PermissionDenied


def internal_access_only(f):
    """
    Decorator to restrict access to views based on internal IP addresses.

    Args:
        f (callable): The view function to decorate.

    Returns:
        callable: Decorated view function.

    Raises:
        PermissionDenied: If the client's IP is not in the list of allowed IPs and the environment is 'staging' or 'prod'.

    """

    def decorate_view(request, *args, **kwargs):
        client_ip, is_routable = get_client_ip(request)
        allowed_ips = [ipaddress.ip_network(ip) for ip in settings.INTERNAL_IPS]
        if settings.ENV in ["staging", "prod"]:
            # Check if the client's IP is not in the allowed IPs
            if not any(ipaddress.ip_address(client_ip) in ip for ip in allowed_ips):
                raise PermissionDenied("You don't have permission to view this page")
        return f(request, *args, **kwargs)

    return decorate_view
