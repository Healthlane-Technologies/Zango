import json
import secrets

from datetime import date, timedelta

from knox.models import AbstractAuthToken
from knox.settings import knox_settings

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db import models
from django.db.models import Q
from django.utils import timezone

from zango.apps.appauth.mixin import UserAuthConfigValidationMixin
from zango.apps.auditlogs.registry import auditlog
from zango.apps.object_store.models import ObjectStore
from zango.apps.shared.platformauth.abstract_model import (
    AbstractOldPasswords,
    AbstractZangoUserModel,
)
from zango.core.model_mixins import FullAuditMixin
from zango.core.utils import get_auth_priority

from ..permissions.mixin import PermissionMixin

# from .perm_mixin import PolicyQsMixin
from ..permissions.models import PolicyGroupModel, PolicyModel
from .schema import get_default_app_user_auth_config, get_default_user_role_auth_config


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
    auth_config = models.JSONField(default=get_default_user_role_auth_config)

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


class AppUserModel(
    AbstractZangoUserModel, PermissionMixin, UserAuthConfigValidationMixin
):
    roles = models.ManyToManyField(UserRoleModel, related_name="users")
    policies = models.ManyToManyField(PolicyModel, related_name="user_policies")
    policy_groups = models.ManyToManyField(
        PolicyGroupModel, related_name="user_policy_groups"
    )
    app_objects = models.JSONField(null=True)
    auth_config = models.JSONField(default=get_default_app_user_auth_config)

    def generate_auth_token(self, role, expiry=knox_settings.TOKEN_TTL):
        try:
            AppUserAuthToken.objects.filter(user=self).delete()
        except Exception:
            pass

        if isinstance(expiry, int):
            expiry = timedelta(seconds=expiry)

        inst, token = AppUserAuthToken.objects.create(
            user=self,
            expiry=expiry,
            prefix=knox_settings.TOKEN_PREFIX,
        )
        if isinstance(role, str):
            role = UserRoleModel.objects.get(name=role)
        elif isinstance(role, int):
            role = UserRoleModel.objects.get(id=role)
        else:
            raise Exception("Specify Role ID or Role name")
        inst.role = role
        inst.save()
        return (inst, token)

    def __str__(self):
        return self.name

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
        import re

        policy = get_auth_priority(policy="password_policy")

        # Default policy if none provided
        default_policy = {
            "min_length": 8,
            "require_numbers": True,
            "require_lowercase": True,
            "require_uppercase": True,
            "require_special_chars": False,
        }

        # Use provided policy or default
        if policy is None:
            policy = default_policy

        # Check minimum length
        min_length = policy.get("min_length", 8)
        if len(password) < min_length:
            return False

        # Build regex pattern based on policy
        regex_parts = []

        # Check for lowercase letters
        if policy.get("require_lowercase", True):
            regex_parts.append(r"(?=.*[a-z])")

        # Check for uppercase letters
        if policy.get("require_uppercase", True):
            regex_parts.append(r"(?=.*[A-Z])")

        # Check for numbers
        if policy.get("require_numbers", True):
            regex_parts.append(r"(?=.*\d)")

        # Check for special characters
        if policy.get("require_special_chars", False):
            regex_parts.append(r"(?=.*[@$!%*#?&])")

        # Combine all lookahead assertions
        regex_pattern = "^" + "".join(regex_parts) + r"[A-Za-z\d@$!#%*?&]+$"

        # Compile and test the regex
        match_re = re.compile(regex_pattern)
        res = re.search(match_re, password)

        return res is not None

    def add_roles(self, role_ids):
        self.roles.clear()
        roles = UserRoleModel.objects.filter(id__in=role_ids)
        self.roles.add(*roles)

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
        password=None,
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
                    if password:
                        if not cls.validate_password(password):
                            message = """
                                Invalid password. Password must follow rules
                                1. Must have at least 8 characters
                                2. Must have at least one uppercase letter
                                3. Must have at least one lowercase letter
                                4. Must have at least one number
                                5. Must have at least one special character
                                """
                            return {
                                "success": success,
                                "message": message,
                                "app_user": app_user,
                            }

                    app_user = cls.objects.create(
                        name=name,
                        email=email,
                        mobile=mobile,
                    )
                    app_user.add_roles(role_ids)

                    if password:
                        app_user.set_password(password)
                    else:
                        app_user.set_unusable_password()

                    if require_verification:
                        app_user.is_active = False
                    else:
                        app_user.is_active = True

                    if password and not force_password_reset:
                        old_password_obj = OldPasswords.objects.create(user=app_user)
                        old_password_obj.setPasswords(app_user.password)
                        old_password_obj.save()

                    if app_objects:
                        app_user.app_objects = app_objects

                    app_user.save()
                    success = True
                    message = "App User created successfully."
            except Exception as e:
                message = str(e)
        return {"success": success, "message": message, "app_user": app_user}

    def update_user(self, data, profile_image=None):
        success = False
        try:
            user_query = Q()
            email = data.get("email")
            mobile = data.get("mobile")
            auth_config = json.loads(data.get("auth_config", "{}"))
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

            self.validate_user_role_two_factor_not_overridden(
                auth_config, self.roles.all()
            )

            if email:
                self.email = email
            if mobile:
                self.mobile = mobile
            if auth_config:
                self.auth_config = auth_config

            name = data.get("name")
            if name:
                self.name = name

            role_ids = data.getlist("roles", [])
            if role_ids:
                self.add_roles(role_ids)

            is_active = data.get("is_active", self.is_active)
            if isinstance(is_active, str):
                is_active = True if is_active == "true" else False

            self.is_active = is_active

            # Handle profile picture update
            if profile_image:
                # Delete old profile pic if exists
                if self.profile_pic:
                    self.profile_pic.delete(save=False)
                self.profile_pic = profile_image

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
        if old_passwords.count() > 0:
            return False
        return True


class OldPasswords(AbstractOldPasswords):
    user = models.ForeignKey(AppUserModel, on_delete=models.PROTECT)

    def clean_old_passwords(self):
        from zango.core.utils import get_auth_priority

        password_policy = get_auth_priority(policy="password_policy", user=self.user)
        password_history_count = password_policy.get("password_history_count", 3)

        old_passwords = OldPasswords.objects.filter(user=self.user).order_by(
            "created_at"
        )
        extra_passwords = old_passwords.count() - password_history_count

        if extra_passwords > 0:
            to_delete = old_passwords[:extra_passwords]
            for old_pw in to_delete:
                old_pw.delete()


class AppUserAuthToken(AbstractAuthToken):
    user = models.ForeignKey(
        AppUserModel,
        null=False,
        blank=False,
        related_name="auth_token_set",
        on_delete=models.CASCADE,
    )
    extra_data = models.JSONField(null=True, blank=True)
    role = models.ForeignKey(
        UserRoleModel,
        null=True,
        blank=True,
        related_name="role",
        on_delete=models.CASCADE,
    )


class OTPCode(FullAuditMixin):
    """
    Model to store various types of One-Time Passwords (OTPs) and login codes for users.
    """

    OTP_TYPE_CHOICES = (
        ("two_factor_auth", "Two-Factor Authentication"),
        ("login_code", "Login Code"),
    )

    user = models.ForeignKey(
        AppUserModel,
        on_delete=models.CASCADE,
        related_name="otp_codes",
    )
    code = models.CharField(
        max_length=128,
    )
    otp_type = models.CharField(
        max_length=50,
        choices=OTP_TYPE_CHOICES,
    )
    is_used = models.BooleanField(
        default=False,
    )
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.name}'s {self.get_otp_type_display()} code ({self.code})"

    def is_valid(self):
        """
        Checks if the OTP code is still valid (not expired and not used).
        """
        return not self.is_used and self.expires_at > timezone.now()

    def mark_as_used(self):
        """
        Marks the OTP code as used.
        """
        self.delete()


def generate_otp(otp_type, user=None, email=None, phone=None, expires_at=5, digits=6):
    try:
        if not user:
            if email:
                user = AppUserModel.objects.filter(email=email).first()
            elif phone:
                user = AppUserModel.objects.filter(mobile=phone).first()

        min_value = 10 ** (digits - 1)
        max_value = 10**digits - 1

        code = str(secrets.randbelow(max_value - min_value + 1) + min_value)
        expires_at = timezone.now() + timezone.timedelta(minutes=expires_at)
        OTPCode.objects.filter(user=user, otp_type=otp_type).delete()
        return OTPCode.objects.create(
            user=user,
            code=code,
            otp_type=otp_type,
            is_used=False,
            expires_at=expires_at,
        ).code
    except Exception as e:
        import traceback

        traceback.print_exc()
        return ""


auditlog.register(AppUserModel, m2m_fields={"policies", "roles", "policy_groups"})
auditlog.register(OldPasswords)
auditlog.register(UserRoleModel, m2m_fields={"policy_groups", "policies"})
auditlog.register(AppUserAuthToken)
auditlog.register(OTPCode, exclude_fields=["code"])
