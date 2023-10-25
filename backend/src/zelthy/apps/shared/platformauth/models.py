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
        _("staff status"),
        default=False,
        help_text="For Django Admin Access. Can be deprecated later",
    )
    is_superadmin = models.BooleanField(
        _("Super Admin"),
        default=False,
        help_text="Is user Super Admin?",
    )
    apps = models.ManyToManyField(
        TenantModel,
        blank=True,
        help_text="User has access to these apps",
    )
    user = models.OneToOneField(
        User, related_name="platform_user", on_delete=models.CASCADE
    )

    USERNAME_FIELD = "email"

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

    def add_apps(self, app_uuids):
        self.apps.clear()
        app_objs = TenantModel.objects.filter(uuid__in=app_uuids)
        self.apps.add(*app_objs)

    @classmethod
    def create_user(
        cls,
        name,
        email,
        mobile,
        password,
        is_superadmin=False,
        force_password_reset=True,
        require_verification=True,
        app_uuids=[],
    ):
        """ """
        success = False
        if not email and not mobile:
            message = "Email and mobile both cannot be empty"
        else:
            try:
                user_query = Q()
                if email:
                    user_query |= Q(email=email)
                if mobile:
                    user_query |= Q(email=email)
                user = PlatformUserModel.objects.filter(user_query)
                if user.exists():
                    message = (
                        "Another user already exists matching the provided credentials"
                    )
                else:
                    if not cls.validate_password(password):
                        message = "Invalid password. Password must follow rules xyz"
                    else:
                        platform_user = cls.objects.create(
                            name=name,
                            email=email,
                            mobile=mobile,
                            is_superadmin=is_superadmin,
                            is_active=True,
                            user=User.objects.create(
                                username=str(uuid.uuid4()),
                                is_active=True,
                                is_staff=True,
                                is_superuser=True,
                            ),
                        )
                        platform_user.set_password(password)
                        platform_user.user.set_unusable_password()
                        if require_verification:
                            platform_user.is_active = False
                        # Add old password logic
                        platform_user.add_apps(app_uuids)
                        platform_user.save()
                        platform_user.user.save()
                        success = True
                        message = "Platform User created successfully."
            except Exception as e:
                message = str(e)
        return {"success": success, "message": message}

    def update_user(self, data):
        success = False
        try:
            user_query = Q()
            email = data.get("email")
            mobile = data.get("mobile")
            if email:
                user_query = user_query | Q(email=email)
            if mobile:
                user_query = user_query | Q(mobile=mobile)
            if user_query:
                user = PlatformUserModel.objects.filter(user_query).exclude(id=self.id)
                if user.exists():
                    message = "Another user already exists matching the provided email or mobile"
                    return {"success": False, "message": message}

            password = data.get("password")
            if password:
                if not self.validate_password(password):
                    message = "Invalid password. Password must follow rules xyz"
                    return {"success": False, "message": message}

                self.set_password(password)

            if email:
                self.email = email
            if mobile:
                self.mobile = mobile

            name = data.get("name")
            if name:
                self.name = name

            app_ids = data.getlist("apps", [])
            if app_ids:
                self.add_apps(app_ids)

            is_active = data.get("is_active", self.is_active)
            if isinstance(is_active, str):
                is_active = True if is_active == "true" else False

            self.is_active = is_active

            self.save()
            success = True
            message = "Platform User updated successfully."
        except Exception as e:
            message = str(e)
        return {"success": success, "message": message}
