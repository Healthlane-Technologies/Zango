from datetime import date, timedelta

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.hashers import check_password

from zelthy.core.model_mixins import FullAuditMixin

from zelthy.apps.object_store.models import ObjectStore
from zelthy.apps.shared.platformauth.abstract_model import AbstractZelthyUserModel


from zelthy.core.model_mixins import FullAuditMixin
from zelthy.apps.shared.platformauth.abstract_model import (
    AbstractZelthyUserModel,
    AbstractOldPasswords,
)

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
    config = models.JSONField(null=True, blank=True)
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


class AppUserModel(AbstractZelthyUserModel, PermissionMixin):
    policies = models.ManyToManyField(PolicyModel, related_name="user_policies")
    policy_groups = models.ManyToManyField(
        PolicyGroupModel, related_name="user_policy_groups"
    )
    app_objects = models.JSONField(null=True)

    def __str__(self):
        return self.name

    def is_user_active(self, role_name=None):
        """
        Check if the user is active.

        Parameters:
        - role_name (str): The name of the role to check for. If provided, the method will check if the user has the specified role and if both the role and the user are active.

        Returns:
        - bool: True if the user is active and, if role_name is provided, the role is active as well. False otherwise.

        """
        if role_name:
            user_role_mapping = self._get_role_mapping(role_name)
            if user_role_mapping:
                return user_role_mapping.is_active and self.is_active
            return False
        return self.is_active

    @property
    def roles(self):
        roles = UserRoleModel.objects.none()
        for user_role in AppUserRoleMappingModel.objects.filter(
            user=self, is_active=True
        ).only("role"):
            roles |= UserRoleModel.objects.filter(pk=user_role.role.pk)
        return roles

    def get_app_object(self, role_id):
        if self.app_objects:
            object_uuid = self.app_objects.get(str(role_id), None)
            if object_uuid:
                return ObjectStore.get_object(object_uuid)
        return None

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
        """
        Add roles to the user.

        Parameters:
        - role_ids (list): A list of role IDs to be added to the user.

        Returns:
        - None

        """
        roles = UserRoleModel.objects.filter(id__in=role_ids)
        assigned_roles = AppUserRoleMappingModel.objects.filter(user=self)
        for role in roles:
            if assigned_roles.filter(role=role).exists():
                assigned_roles.filter(role=role).update(is_active=True)
            else:
                AppUserRoleMappingModel.objects.create(user=self, role=role)

    def remove_roles(self, role_ids):
        """
        Remove roles from the user.

        Parameters:
        - role_ids (list): A list of role IDs to be removed from the user.

        Returns:
        - None
        """
        roles = UserRoleModel.objects.filter(id__in=role_ids)
        for role in roles:
            AppUserRoleMappingModel.objects.filter(user=self, role=role).delete()

    def update_roles(self, role_ids):
        """
        Update the roles of the user by deleting all existing roles and adding new ones.
        This effectively replaces the user's roles with the new set of roles provided.

        Parameters:
        - role_ids (list): A list of role IDs to be assigned to the user. These IDs replace any existing roles the user has.

        Returns:
        - None
        """

        AppUserRoleMappingModel.objects.filter(user=self).delete()
        roles = UserRoleModel.objects.filter(id__in=role_ids)
        for role in roles:
            AppUserRoleMappingModel.objects.create(user=self, role=role)

    def check_password_validity(self, password):
        """
        Does not allow a password from within PASSWORD_NO_REPEAT_DAYS
        """
        minDate = date.today() - timedelta(settings.PASSWORD_NO_REPEAT_DAYS)
        old_pwds = self.oldpasswords_set.all().filter(password_date__gte=minDate)
        matchFound = False
        for p in old_pwds:
            if check_password(password, p.getPasswords()):
                matchFound = True
                break
        return matchFound

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
        app_objects=None,
    ):
        """ """
        success = False
        app_user = None
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
                    if password and not cls.validate_password(password):
                        message = """
                            Invalid password. Password must follow rules
                            1. Must have at least 8 characters
                            2. Must have at least one uppercase letter
                            3. Must have at least one lowercase letter
                            4. Must have at least one number
                            5. Must have at least one special character
                            """
                    else:
                        app_user = cls.objects.create(
                            name=name,
                            email=email,
                            mobile=mobile,
                        )
                        app_user.add_roles(role_ids)
                        if password:
                            app_user.set_password(password)
                        else:
                            app_user.set_unusable_password()  # Ask Rajat

                        if require_verification:
                            app_user.is_active = False
                        else:
                            app_user.is_active = True

                        if not force_password_reset:
                            old_password_obj = OldPasswords.objects.create(user=user)
                            old_password_obj.setPasswords(user.password)
                            old_password_obj.save()

                        if app_objects:
                            app_user.app_objects = app_objects

                        app_user.save()
                        success = True
                        message = "App User created successfully."
            except Exception as e:
                message = str(e)
        return {"success": success, "message": message, "app_user": app_user}

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
                user = AppUserModel.objects.filter(user_query).exclude(id=self.id)
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

            role_ids = data.getlist("roles", [])
            if role_ids:
                self.update_roles(role_ids)

            is_active = data.get("is_active", self.is_active)
            if isinstance(is_active, str):
                is_active = True if is_active == "true" else False

            self.is_active = is_active

            self.save()
            success = True
            message = "App User updated successfully."
        except Exception as e:
            message = str(e)
        return {"success": success, "message": message}

    def has_role_step(self, request):
        """
        Checks if role step is part of user login process
        If only one role then don't show
        show if 0 or >1 roles
        """
        roles = self.roles.filter(is_active=True)
        if roles.count() == 1:
            return False
        return True

    def has_password_reset_step(self, request, days=90):
        """
        Checks if password reset is required as part of login process
        If password was not changed in last 90 days, force password reset
        """
        if days == -1:
            return False
        old_passwords = self.oldpasswords_set.all().filter(
            password_date__gt=date.today() - timedelta(days)
        )
        print(old_passwords)
        if old_passwords.count() > 0:
            return False
        return True

    def _get_role_mapping(self, role_name):
        try:
            return AppUserRoleMappingModel.objects.get(user=self, role__name=role_name)
        except:
            pass

    def has_role(self, role_name):
        """
        Checks if the user has a specific role.

        Parameters:
        - role_name (str): The name of the role to check for.

        Returns:
        - bool: True if the user has the specified role, False otherwise.
        """
        user_role_mapping = self._get_role_mapping(role_name=role_name)
        return True if user_role_mapping and user_role_mapping.is_active else False

    def activate(self, role_name=None):
        """
        Activate the user or a specific role.

        Parameters:
        - role_name (str, optional): The name of the role to activate. If provided, only the specified role will be activated. If not provided, user will be activated.

        Returns:
        - None

        """
        if role_name:
            user_role_mapping = self._get_role_mapping(role_name)
            if user_role_mapping:
                user_role_mapping.is_active = True
                user_role_mapping.save(update_fields=["is_active"])
        else:
            self.is_active = True
            self.save(update_fields=["is_active"])

    def deactivate(self, role_name=None):
        """
        Deactivates the user or a specific role.

        Parameters:
        - role_name (str, optional): The name of the role to deactivate. If provided, only the specified role will be deactivated. If not provided, user will be deactivated.

        Returns:
        - None

        """
        if role_name:
            user_role_mapping = self._get_role_mapping(role_name)
            if user_role_mapping:
                user_role_mapping.is_active = False
                user_role_mapping.save(update_fields=["is_active"])
        else:
            self.is_active = False
            self.save(update_fields=["is_active"])

    @classmethod
    def filter_users(cls, query):
        """
        Filter users based on the provided query parameters.

        Parameters:
        - query (dict): A dictionary containing the query parameters to filter the users. The keys of the dictionary should correspond to the field names of the User model, and the values should be the desired values for those fields.

        Returns:
        - QuerySet: A QuerySet containing the filtered users.

        """
        return cls.objects.filter(**query)


class OldPasswords(AbstractOldPasswords):
    user = models.ForeignKey(AppUserModel, on_delete=models.PROTECT)


class AppUserRoleMappingModel(FullAuditMixin):

    user = models.ForeignKey(
        AppUserModel, related_name="app_user", on_delete=models.CASCADE
    )
    role = models.ForeignKey(
        UserRoleModel, related_name="app_user_role", on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)
