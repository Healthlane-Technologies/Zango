


class PolicyQsMixin:

  def is_ip_valid(self, request, permission):
    # TODO: Handle Global Whitelist IPs,allow all, CIDR, etc.
    return request.META["REMOTE_ADDR"] in permission.get("accessIP")

  def is_accessTime_valid(self, request, permission):
    """
      True if accessTime is not specified else validate
    """
    #TODO
    return True
  
  def has_view_access(self, permission, view_name):
    if permission.get("type") == "view":
      if permission.get("name") == view_name:
        return True
    return False


  def get_policies(self, perm_type, view=None, dataModel=None):
    from django.utils import timezone
    policy_groups = self.policy_groups.all()
    policies_qs = self.policies.all() | PolicyModel.objects.filter(policy_groups__in=policy_groups)
    valid_policies_qs = policies_qs.filter(is_active=True, expiry__gte=timezone.now())
    if perm_type == "userAccess":
      qs = valid_policies_qs.filter(
          statement__permissions__contains=[{"type": perm_type}]
          )
    elif perm_type == "view":
      qs = valid_policies_qs.filter(
          statement__permissions__contains=[{"type": perm_type, "name": view}]
          )
    elif perm_type == "dataModel":
      qs = valid_policies_qs.filter(
          statement__permissions__contains=[{"type": perm_type, "name": dataModel}]
          )
    else:
      qs = PolicyModel.objects.none()
    return qs
  
  def has_perm(self, request, perm_type, view_name=None, dataModel=None):
    """
      checks if the role or user has the permission
    """
    policies =  self.get_policies(perm_type, view_name, dataModel)
    if not policies.exists():
      return False
    if perm_type == "userAccess":
      for policy in policies:
        permissions = policy.statement.get("permissions")
        for permission in permissions:
          if self.is_ip_valid(request, permission) and self.is_accessTime_valid(request, permission):
            return True
    elif perm_type == "view":
      for policy in policies:
        permissions = policy.statement.get("permissions")
        for permission in permissions:
          if self.has_view_access(permission, view_name):
            return True
    elif perm_type == "dataModel":
      pass