from django.conf import settings
from django.http import Http404
from ipware.ip import get_client_ip


def internal_access_only(f):
    def decorate_view(request, *args, **kwargs):
        client_ip, is_routable = get_client_ip(request)
        if (
            settings.ENV in ["staging", "prod"]
            and not client_ip in settings.INTERNAL_IPS
        ):
            raise Http404
        return f(request, *args, **kwargs)

    return decorate_view
