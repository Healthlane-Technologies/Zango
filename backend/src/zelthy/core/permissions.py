from rest_framework.permissions import IsAuthenticated
from .common_utils import get_client_ip
from django.core import exceptions


class CheckIPWhitelisting:
    def check_ipwhitelisting(self, request):
        # TODO: Add whitelist_ips field in tenant model
        return True
        if not request.tenant.whitelist_ips:
            return True
        client_ip = get_client_ip(request)

        whitelisted = request.tenant.whitelist_ips.split(",")
        whitelisted = [w.strip() for w in whitelisted]
        if client_ip in whitelisted:
            return True
        return False


class IsAuthenticatedPlatformUser(IsAuthenticated, CheckIPWhitelisting):
    def has_permission(self, request, view):
        if not self.check_ipwhitelisting(request):
            return False
        if super(IsAuthenticatedPlatformUser, self).has_permission(request, view):
            try:
                platform_user = request.user.platform_user
                if (
                    platform_user.__class__.__name__ == "PlatformUserModel"
                    and platform_user.is_active
                ):
                    return True
            except:
                return False
        return False


class IsAuthenticatedAppUser(IsAuthenticated, CheckIPWhitelisting):
    def has_permission(self, request, view):
        if super(IsAuthenticatedAppUser, self).has_permission(request, view):
            try:
                app_user = request.user
                if app_user.__class__.__name__ == "AppUserModel" and app_user.is_active:
                    return True
            except:
                return False
        return False


class IsSuperAdminPlatformUser(IsAuthenticatedPlatformUser):
    def has_permission(self, request, view):
        has_perm = super(IsSuperAdminPlatformUser, self).has_permission(request, view)
        if has_perm:
            platform_user = request.user.platform_user
            if platform_user.is_superadmin:
                return True

        return False


class IsPlatformUserAllowedApp(IsAuthenticatedPlatformUser):
    def has_permission(self, request, view):
        has_perm = super(IsPlatformUserAllowedApp, self).has_permission(request, view)
        if has_perm:
            platform_user = request.user.platform_user
            if platform_user.is_superadmin:
                return True

            app_uuid = view.kwargs.get("app_uuid")
            allowed_apps = platform_user.apps.all()
            if allowed_apps.filter(uuid=app_uuid).exists():
                return True

        return False
