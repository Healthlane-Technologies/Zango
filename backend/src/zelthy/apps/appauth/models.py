import uuid
from django.db import models
from django.db.models import Q
from zelthy.core.model_mixins import FullAuditMixin
from zelthy.apps.shared.platformauth.abstract_model import AbstractZelthyUserModel

from django.contrib.auth.models import User
from django.db.models import JSONField

from zelthy.core.model_mixins import FullAuditMixin
from zelthy.apps.shared.platformauth.abstract_model import AbstractZelthyUserModel
from ..permissions.models import PolicyModel, PolicyGroupModel

# from .perm_mixin import PolicyQsMixin
from ..permissions.mixin import PermissionMixin


class UserRoleModel(FullAuditMixin, PermissionMixin):
    name = models.CharField("Unique Name of the User Role", max_length=50, unique=True)
    policies = models.ManyToManyField(
        PolicyModel, related_name="role_policies", blank=True
    )
    policy_groups = models.ManyToManyField(
        PolicyGroupModel, related_name="role_policy_groups", blank=True
    )
    config = JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def no_of_users(self):
        return self.users.all().count()

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
    roles = models.ManyToManyField(UserRoleModel, related_name="users")
    user = models.OneToOneField(User, related_name="app_user", on_delete=models.CASCADE)
    policies = models.ManyToManyField(PolicyModel, related_name="user_policies")
    policy_groups = models.ManyToManyField(
        PolicyGroupModel, related_name="user_policy_groups"
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

    def add_roles(self, role_ids):
        roles = UserRoleModel.objects.filter(id__in=role_ids)
        self.roles.add(*roles)

    @classmethod
    def create_user(
        cls,
        name,
        email,
        mobile,
        password,
        role_ids=[],
        force_password_reset=True,
        require_verification=True,
    ):
        """ """
        success = False
        if not email and not mobile:
            message = "Email and mobile both cannot be empty"
        else:
            try:
                user_query = Q()
                if email:
                    user_query = user_query | Q(email=email)
                if mobile:
                    user_query = user_query | Q(mobile=mobile)

                user = cls.objects.filter(user_query)
                if user.exists():
                    message = (
                        "Another user already exists matching the provided credentials"
                    )
                else:
                    if not cls.validate_password(password):
                        message = "Invalid password. Password must follow rules xyz"
                    else:
                        app_user = cls.objects.create(
                            name=name,
                            email=email,
                            mobile=mobile,
                            user=User.objects.create(
                                username=str(uuid.uuid4()), is_active=True
                            ),
                        )
                        app_user.add_roles(role_ids)
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

            user = AppUserModel.objects.filter(user_query).exclude(id=self.id)
            print("user: ", user)
            if user.exists():
                message = (
                    "Another user already exists matching the provided email or mobile"
                )
                return {"success": False, "message": message}

            password = data.get("password")
            if password:
                if not self.validate_password(password):
                    message = "Invalid password. Password must follow rules xyz"
                    return {"success": False, "message": message}

                self.set_password(password)
                ##Add old password logic, force_reset

            if email:
                self.email = email
            if mobile:
                self.mobile = mobile

            name = data.get("name")
            if name:
                self.name = name

            role_ids = data.get("roles", [])
            if role_ids:
                self.add_roles(role_ids)

            is_active = data.get("is_active", self.is_active)
            self.is_active = is_active

            self.save()
            success = True
            message = "App User updated successfully."
        except Exception as e:
            message = str(e)
        return {"success": success, "message": message}
