import uuid
from django.db import models
from django.db.models import Q
from zelthy3.backend.core.model_mixins import FullAuditMixin
from zelthy3.backend.apps.shared.platformauth.abstract_model import AbstractZelthyUserModel
from knox.models import AuthToken

from django.contrib.auth.models import User
from django.db.models import JSONField

from zelthy3.backend.core.model_mixins import FullAuditMixin
from zelthy3.backend.apps.shared.platformauth.abstract_model import AbstractZelthyUserModel

class UserRoleModel(FullAuditMixin):

  name = models.CharField(
                "Unique Name of the User Role",
                max_length = 50,
                unique=True
                )  
  config = JSONField(
                null=True,
                blank=True
                )
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

# class UserRoleTokenModel(models.Model):
#   token = models.ForeignKey(
#                       AuthToken,
#                       on_delete=models.CASCADE
#                       )
#   role = models.ForeignKey(
#                       UserRoleModel,
#                       on_delete=models.CASCADE
#                       )

#   def __str__(self):
#     return self.token

class AppUserModel(AbstractZelthyUserModel):
    
  roles = models.ManyToManyField(UserRoleModel)
  user = models.OneToOneField(
                        User,
                        related_name='app_user',
                        on_delete=models.CASCADE
                        )


  def __str__(self):
    return self.name

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



