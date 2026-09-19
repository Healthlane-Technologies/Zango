from django.core import signing

from zango.apps.shared.platformauth.models import PlatformUserModel


# Lifetime of the signed platform-user token passed as ?token=. It is minted
# once at the start of an Agent Mode run but first used at STEP 5h, route and
# menu registration, which is the last step of the build -- a 34-minute run
# reached it 34 seconds after a 1800s token had expired, so every call
# redirected to /login/ and the app shipped with no navigation while the run
# still reported success. Two hours covers a full build with headroom.
TOKEN_MAX_AGE_SECONDS = 7200


def get_platform_user(request):
    try:
        token = request.GET.get("token", None)
        user_id = signing.loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
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
