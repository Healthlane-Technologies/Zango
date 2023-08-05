import uuid
from django.db import models
from django.db.models import Q
from zelthy3.backend.core.model_mixins import FullAuditMixin
from zelthy3.backend.apps.shared.platformauth.abstract_model import AbstractZelthyUserModel

from django.contrib.auth.models import User
from django.db.models import JSONField

from zelthy3.backend.core.model_mixins import FullAuditMixin
from zelthy3.backend.apps.shared.platformauth.abstract_model import AbstractZelthyUserModel
from ..permissions.models import PolicyModel, PolicyGroupModel

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



          


class UserRoleModel(FullAuditMixin, PolicyQsMixin):

  name = models.CharField(
                "Unique Name of the User Role",
                max_length = 50,
                unique=True
                )
  policies = models.ManyToManyField(
                PolicyModel,
                related_name="role_policies",
                blank=True
                )
  policy_groups = models.ManyToManyField(
                PolicyGroupModel,
                related_name="role_policy_groups",
                blank=True
                )
  config = JSONField(
                null=True,
                blank=True
                )
  temp_field = models.CharField(max_length=20, null=True)
  is_default = models.BooleanField(default=False)
  """
    sample config
      {'mfa': {'enabled': True, 'method': 'totp', 'allow_bypass': True, 'bypass_carry_forward_days': 7},
      'auth_token': {'enabled': true, 'default_ttl': 10}, # default expiry in hours
      'whitelist_ips': '',
      'disable_password': False,
      'password_policy': {'rules': [], 'reset_days': 90},
      'frame': {'name': '', 'api_level': 5, 'config': {}}
      }
    
  """

  def __str__(self):
      return self.name
  
  def save(self, *args, **kwargs):
      if self.pk and self.is_default:
          # Prevent modification of the default object's name
          default_obj = UserRoleModel.objects.get(pk=self.pk)
          self.name = default_obj.name
      super().save(*args, **kwargs)
  
  def delete(self, *args, **kwargs):
      if self.is_default:
          # Prevent deletion of the default object
          raise ValueError("Cannot delete the default object.")
      super().delete(*args, **kwargs)



    
          


class AppUserModel(AbstractZelthyUserModel, PolicyQsMixin):
    
  roles = models.ManyToManyField(UserRoleModel)
  user = models.OneToOneField(
                        User,
                        related_name='app_user',
                        on_delete=models.CASCADE
                        )
  policies = models.ManyToManyField(
                PolicyModel,
                related_name="user_policies"
                )
  policy_groups = models.ManyToManyField(
                PolicyGroupModel,
                related_name="user_policy_groups"
                )


  def __str__(self):
    return self.name
    
  def has_perm(self, request, perm_type, view=None, dataModel=None):
    if perm_type == "userAccess":
      pass
    elif perm_type == "view":
      pass
    elif perm_type == "dataModel":
      pass
      
    

  @classmethod
  def validate_password(cls, password):
    """
    Password Rule for App Users: Maintain the rule in AppConfig or use default
    {
        'password_rule': {}
    }
    """
    import re
    reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,18}$"
    match_re = re.compile(reg)
    res = re.search(match_re, password)
    if res:
      return True
    return False


  @classmethod
  def create_user(cls, name, email, mobile, password, 
            force_password_reset=True, require_verification=True):
    """
     
    """
    success = False    
    if not email and not mobile:
      message = "Email and mobile both cannot be empty"
    else:
      try:
        user =  cls.objects.filter(
                 Q(email=email) | Q(mobile=mobile)
             )
        if user.exists():
          message = "Another user already exists matching the provided credentials"
        else:
          if not cls.validate_password(password):
            message = "Invalid password. Password must follow rules xyz"
          else:
            app_user = cls.objects.create(
                        name=name,
                        email=email,
                        mobile=mobile,
                        user=User.objects.create(username=str(uuid.uuid4()), is_active=True)
                        )
            app_user.set_password(password)
            app_user.user.set_unusable_password()
            if require_verification:
              app_user.is_active = False
            ##Add old password logic
            app_user.save()
            app_user.user.save()
            success = True
            message = "App User created successfully."            
      except Exception as e:
        message = str(e)
    return {'success': success, 'message': message}



