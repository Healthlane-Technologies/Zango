from django.core import signing

from zelthy.apps.shared.platformauth.models import PlatformUserModel


def is_platform_user(request):
    try:
        token = request.GET.get("token", None)
        user_id = signing.loads(token, max_age=1800)
        user = PlatformUserModel.objects.get(id=user_id)
        tenant_id = request.tenant.id
        if user.is_active:
            if user.is_superadmin:
                return True
            if user.apps.filter(id=tenant_id):
                return True
        return False
    except Exception:
        return False
