import uuid
from django.db import models
from django.db.models import Q

from django.contrib.auth.models import AbstractBaseUser
# from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from django.contrib.auth.models import User

from zelthy.apps.shared.tenancy.models import TenantModel

from .abstract_model import AbstractZelthyUserModel

from zelthy.core.model_mixins import FullAuditMixin

class PlatformUserModel(AbstractZelthyUserModel):
  is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text='For Django Admin Access. Can be deprecated later',
    )
  apps = models.ManyToManyField(
                        TenantModel,
                        blank=True,
                        help_text='User has access to these apps',
                        )
  user = models.OneToOneField(
                        User,
                        related_name='platform_user',
                        on_delete=models.CASCADE
                        )

  USERNAME_FIELD = 'email'

  # AUTH_USER_MODEL = "platformauth.PlatformUserModel"

  def __str__(self):
    return self.name

  def has_module_perms(self, module):
    """
    for django admin access; deprecate later
    """
    return True
  
  def has_perm(self, app):
    """
    for django admin access; deprecate later
    """
    return True

  @classmethod
  def validate_password(cls, password):
    """
    Password Rule for Platform Users: 8-18 charecters; At least one upper case, number 
    and special charecter
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
        user = PlatformUserModel.objects.filter(
                 Q(email=email) | Q(mobile=mobile)
             )
        if user.exists():
          message = "Another user already exists matching the provided credentials"
        else:
          if not cls.validate_password(password):
            message =  "Invalid password. Password must follow rules xyz"
          else:
            platform_user = cls.objects.create(
                        name=name,
                        email=email,
                        mobile=mobile,
                        user=User.objects.create(username=str(uuid.uuid4()), is_active=True)
                        )
            platform_user.set_password(password)
            platform_user.user.set_unusable_password()
            if require_verification:
              platform_user.is_active = False
            ##Add old password logic
            platform_user.save()
            platform_user.user.save()
            success = True
            message = "Platform User created successfully."            
      except Exception as e:
        message = str(e)
    return {'success': success, 'message': message}




