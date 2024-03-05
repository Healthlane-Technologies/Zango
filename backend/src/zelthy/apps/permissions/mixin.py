import ipaddress
from django.utils import timezone
from django.db.models import Q
from .models import PermissionsModel, PolicyModel


class PermissionMixin:
    """
    Mixin class to check if permission exists for the requested resource.
    The Objects that are accessing resources for which permission checks
    needs to be run can be either a User Roles or a User. Typically Users
    get access to resources through their User Role for which the current
    session has been granted. Accordingly, this mixin class is subclassed
    by UserRoleModel or AppUserModel.

    Resources can be either a view or a model object. By default there
    is no access to any resource in an application. Applications have two
    ways of accessing resources, either as a request coming from browser
    client or as a celery task.

    - Requests: userAccess permission will be checked followed
    by view permission. Any ORM queries inside the view will be seperately
    perm checked.

    - Tasks: All tasks must be owned by a user role. The user role must have
    permission for all the resouces accessed by the task (typically model objects)

    """

    def is_ip_valid(self, request, permission):
        if permission.get("type") == "userAccess":
            try:
                allowed_ips = [
                    ipaddress.ip_network(ip) for ip in permission.get("accessIP", [])
                ]
                for ip in allowed_ips:
                    if ipaddress.ip_address(request.META["REMOTE_ADDR"]) in ip:
                        return True
            except:
                pass
        return False

    def has_view_access(self, permission, view_name):
        if permission.get("type") == "view":
            if permission.get("name") == view_name:
                return True
        return False

    def get_anonymous_userrole_policies(self):
        """
        Get the anonymous userrole policies.

        :return: QuerySet of anonymous userrole policies
        """
        anonymous_userrole_policies = self.__class__.objects.get(
            name="AnonymousUsers"
        ).policies.filter(
            Q(is_active=True, expiry__gte=timezone.now())
            | Q(is_active=True, expiry__isnull=True)
        )
        return anonymous_userrole_policies

    def get_policies(self, perm_type, view=None, model=None):
        policy_groups = self.policy_groups.all()
        policies_qs = self.policies.all() | PolicyModel.objects.filter(
            policy_groups__in=policy_groups
        )
        valid_policies_qs = policies_qs.filter(
            Q(is_active=True, expiry__gte=timezone.now())
            | Q(is_active=True, expiry__isnull=True)
        )
        if perm_type == "userAccess":
            qs = valid_policies_qs.filter(
                statement__permissions__contains=[{"type": perm_type}]
            )
        elif perm_type == "view":
            # If current user role is not anonymous, include anonymous user role policies
            # as non-anonymous user role can access views available to anonymous user role.
            if self.name != "AnonymousUsers":
                anonymous_userrole_policies = self.get_anonymous_userrole_policies()
                valid_policies_qs = valid_policies_qs | anonymous_userrole_policies
            qs = valid_policies_qs.filter(
                statement__permissions__contains=[{"type": perm_type, "name": view}]
            )
        elif perm_type == "model":
            qs = valid_policies_qs.filter(
                statement__permissions__contains=[{"type": perm_type, "name": model}]
            )
        else:
            qs = PolicyModel.objects.none()
        return qs

    def has_perm(self, request, perm_type, view_name=None):
        """
        checks if the role or user has the permission
        """
        policies = self.get_policies(perm_type, view_name)
        if not policies.exists():
            return False
        if perm_type == "userAccess":
            for policy in policies:
                permissions = policy.statement.get("permissions")
                for permission in permissions:
                    if self.is_ip_valid(request, permission):
                        return True
        elif perm_type == "view":
            for policy in policies:
                permissions = policy.statement.get("permissions")
                for permission in permissions:
                    if self.has_view_access(permission, view_name):
                        return True
        return False

    def get_model_perms(self, model):
        policy_groups = self.policy_groups.all()
        policies_qs = self.policies.all() | PolicyModel.objects.filter(
            policy_groups__in=policy_groups
        )
        valid_policies_qs = policies_qs.filter(
            Q(is_active=True, expiry__gte=timezone.now())
            | Q(is_active=True, expiry__isnull=True)
        )
        qs = valid_policies_qs.filter(
            statement__permissions__contains=[{"name": model}]
        )
        return qs
