from django.core import signing

from zango.apps.shared.platformauth.models import PlatformUserModel


def get_platform_user(request):
    try:
        token = request.GET.get("token", None)
        user_id = signing.loads(token, max_age=1800)
        return PlatformUserModel.objects.get(id=user_id)
    except Exception:
        return None


def is_platform_user(request):
    try:
        user = get_platform_user(request)
        tenant_id = request.tenant.id
        if user.is_active:
            if user.is_superadmin:
                return True
            if user.apps.filter(id=tenant_id):
                return True
        return False
    except Exception:
        return False
