import json
import secrets

from datetime import date, timedelta

from knox.models import AbstractAuthToken
from knox.settings import knox_settings

from django.contrib.auth.hashers import check_password
from django.db import connection, models
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
    def validate_password(cls, password, tenant):
        import re

        policy = get_auth_priority(policy="password_policy", tenant=tenant)

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
        Validates that the new password doesn't match recent or historical passwords.

        Checks against two policies:
        1. PASSWORD_NO_REPEAT_DAYS: Password history within N days
        2. PASSWORD_HISTORY_COUNT: Last N password hashes

        Args:
            password (str): The new password to validate

        Returns:
            dict: {"validation": bool, "message": str} if validation fails,
                  None if validation passes
        """
        if not password or not isinstance(password, str):
            return {
                "validation": False,
                "message": "Password must be a non-empty string",
            }

        password_policy = get_auth_priority(policy="password_policy", user=self)
        history_count = password_policy.get("password_history_count", 3)
        no_repeat_days = password_policy.get("password_repeat_days", 180)

        # Check password against time-based history (within no_repeat_days)
        if no_repeat_days > 0:
            min_date = date.today() - timedelta(days=no_repeat_days)
            recent_passwords = self.oldpasswords_set.filter(password_date__gte=min_date)

            if self._check_password_in_history(password, recent_passwords):
                return {
                    "validation": False,
                    "message": f"New password must not be the same as any password used in the previous {no_repeat_days} days",
                }

        # Check password against count-based history (last N passwords)
        if history_count > 0:
            historical_passwords = self.oldpasswords_set.all().order_by(
                "-password_date"
            )[:history_count]

            if self._check_password_in_history(password, historical_passwords):
                return {
                    "validation": False,
                    "message": f"New password must not be the same as the last {history_count} passwords",
                }

        # Password is valid
        return {"validation": True, "message": "Password is valid"}

    def _check_password_in_history(self, password, password_records):
        """
        Helper method to check if password matches any in the given records.

        Args:
            password (str): Plain text password to check
            password_records: QuerySet of OldPasswords records

        Returns:
            bool: True if password matches any record, False otherwise
        """
        for old_password_record in password_records:
            try:
                stored_hash = old_password_record.getPasswords()
                if check_password(password, stored_hash):
                    return True
            except (json.JSONDecodeError, ValueError, TypeError):
                # Log corrupted password record but continue checking others
                # Consider marking this record as corrupted for maintenance
                continue
        return False

    @classmethod
    def should_set_password(cls, tenant, role_ids):
        for role in UserRoleModel.objects.filter(id__in=role_ids):
            if role.auth_config.get("enforce_sso", False):
                return False, "Password cannot be set since SSO is enforced"
        login_methods = get_auth_priority(policy="login_methods", tenant=tenant)
        if login_methods.get("password", {}).get("enabled", False):
            return True, "Can set password"
        return False, "Password cannot be set since password based login is not enabled"

    @classmethod
    def create_user(
        cls,
        name,
        email=None,
        mobile=None,
        password=None,
        role_ids=[],
        force_password_reset=True,
        require_verification=True,
        app_objects=None,
        auth_config=None,
        tenant=None,
    ):
        success = False
        app_user = None

        # Validate all inputs before creating user
        if not email and not mobile:
            message = "Email and mobile both cannot be empty"
            return {"success": success, "message": message, "app_user": app_user}

        try:
            # Check for existing user with same email or mobile
            existing_fields = []
            if email and cls.objects.filter(email__iexact=email).exists():
                existing_fields.append("email")
            if mobile and cls.objects.filter(mobile=mobile).exists():
                existing_fields.append("mobile")

            if existing_fields:
                field_text = " and ".join(existing_fields)
                message = f"User with the same {field_text} already exists"
                return {"success": success, "message": message, "app_user": app_user}

            # Validate roles exist
            existing_roles = None
            if role_ids:
                existing_roles = UserRoleModel.objects.filter(id__in=role_ids)
                if len(role_ids) != existing_roles.count():
                    message = "One or more specified role IDs do not exist"
                    return {
                        "success": success,
                        "message": message,
                        "app_user": app_user,
                    }

            should_set_password, err_msg = cls.should_set_password(tenant, role_ids)

            # Validate password if provided
            if password:
                if not should_set_password:
                    return {
                        "success": success,
                        "message": err_msg,
                        "app_user": app_user,
                    }
                if not cls.validate_password(password, tenant):
                    password_policy = get_auth_priority(
                        policy="password_policy", tenant=tenant
                    )
                    message = f"""
                        Password should meet the following requirements: 
                        Minimum Length: {password_policy.get("min_length", 8)}
                        Require Numbers: {password_policy.get("require_numbers", True)}
                        Require Symbols: {password_policy.get("require_symbols", True)}
                        Require Uppercase: {password_policy.get("require_uppercase", True)}
                        Require Lowercase: {password_policy.get("require_lowercase", True)}
                    """
                    return {
                        "success": success,
                        "message": message,
                        "app_user": app_user,
                    }
            else:
                if should_set_password:
                    message = "Password cannot be empty"
                    return {
                        "success": success,
                        "message": message,
                        "app_user": app_user,
                    }

            # All basic validations passed, now create the user
            app_user = cls.objects.create(
                name=name,
                email=email,
                mobile=mobile,
            )

            # Add roles first so they're available for auth_config validation
            if role_ids:
                app_user.add_roles(role_ids)

            # Set auth_config and validate it with the actual user and roles
            final_auth_config = (
                auth_config if auth_config else get_default_app_user_auth_config()
            )
            app_user.auth_config = final_auth_config

            # Validate auth_config with the saved user and roles
            try:
                app_user.validate_auth_config(
                    final_auth_config,
                    app_user,
                    existing_roles or UserRoleModel.objects.none(),
                    tenant or connection.tenant,
                )
            except Exception as e:
                app_user.delete()
                message = str(e)
                return {"success": False, "message": message, "app_user": None}

            # Set password
            if password:
                app_user.set_password(password)
            else:
                app_user.set_unusable_password()

            # Set active status
            if require_verification:
                app_user.is_active = False
            else:
                app_user.is_active = True

            # Handle old password tracking
            if password and not force_password_reset:
                old_password_obj = OldPasswords.objects.create(user=app_user)
                old_password_obj.setPasswords(app_user.password)
                old_password_obj.save()

            # Set app_objects
            if app_objects:
                app_user.app_objects = app_objects

            app_user.save()
            success = True
            message = "App User created successfully."

        except Exception as e:
            import traceback

            message = traceback.format_exc()
            # If user was created but validation failed later, clean up
            if app_user and app_user.pk:
                try:
                    app_user.delete()
                except Exception:
                    pass
                app_user = None

        return {"success": success, "message": message, "app_user": app_user}

    def update_user(self, data, profile_image=None, tenant=None):
        success = False

        try:
            # Extract and validate all inputs first
            email = data.get("email")
            mobile = data.get("mobile")
            password = data.get("password")
            name = data.get("name")
            role_ids = data.getlist("roles", [])
            is_active = data.get("is_active", self.is_active)
            auth_config = json.loads(data.get("auth_config", "{}"))

            if password:
                if any(
                    role.auth_config.get("enforce_sso", False)
                    for role in self.roles.all()
                ):
                    return {
                        "success": False,
                        "message": "User password cannot be updated when SSO is enforced",
                    }

            # Validate email/mobile uniqueness
            existing_fields = []
            if (
                email
                and AppUserModel.objects.filter(email__iexact=email)
                .exclude(id=self.id)
                .exists()
            ):
                existing_fields.append("email")
            if (
                mobile
                and AppUserModel.objects.filter(mobile=mobile)
                .exclude(id=self.id)
                .exists()
            ):
                existing_fields.append("mobile")

            if existing_fields:
                field_text = " and ".join(existing_fields)
                message = f"User with the same {field_text} already exists"
                return {"success": False, "message": message}

            # Validate password if provided
            if password:
                if not self.validate_password(password, tenant):
                    message = f"""
                        Password should meet the following requirements: 
                        Minimum Length: {get_auth_priority(policy="password_policy", tenant=tenant).get("min_length", 8)}
                        Require Numbers: {get_auth_priority(policy="password_policy", tenant=tenant).get("require_numbers", True)}
                        Require Symbols: {get_auth_priority(policy="password_policy", tenant=tenant).get("require_symbols", True)}
                        Require Uppercase: {get_auth_priority(policy="password_policy", tenant=tenant).get("require_uppercase", True)}
                        Require Lowercase: {get_auth_priority(policy="password_policy", tenant=tenant).get("require_lowercase", True)}
                    """
                    return {"success": False, "message": message}

            # Validate roles exist if provided
            new_roles = None
            if role_ids:
                new_roles = UserRoleModel.objects.filter(id__in=role_ids)
                if len(role_ids) != new_roles.count():
                    message = "One or more specified role IDs do not exist"
                    return {"success": False, "message": message}

            # Validate is_active format
            if isinstance(is_active, str):
                is_active = True if is_active == "true" else False

            # All basic validations passed, now apply changes
            if email:
                self.email = email
            if mobile:
                self.mobile = mobile
            if name:
                self.name = name
            if password:
                self.set_password(password)
            if role_ids:
                self.add_roles(role_ids)

            self.is_active = is_active

            # Set auth_config after roles are updated and validate
            if auth_config:
                self.auth_config = auth_config
                # Use the updated roles or existing roles for validation
                roles_for_validation = new_roles if role_ids else self.roles.all()
                self.validate_auth_config(
                    auth_config, self, roles_for_validation, tenant
                )

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

    def get_active_sessions(self):
        """
        Returns active sessions and tokens for the user with detailed information
        including generated_at, location (IP), browser_agent, etc.

        Returns:
            dict: Contains 'sessions' and 'tokens' with their respective details
        """
        from zango.apps.accesslogs.models import AppAccessLog

        result = {"sessions": [], "tokens": []}

        # Get active sessions from AppAccessLog
        active_sessions = AppAccessLog.objects.filter(
            user=self, is_login_successful=True, session_expired_at__isnull=True
        ).order_by("-attempt_time")

        for session in active_sessions:
            session_data = {
                "id": session.id,
                "generated_at": timezone.localtime(session.attempt_time).strftime(
                    "%Y-%m-%d %H:%M:%S %Z"
                ),
                # 'generated_at_raw': session.attempt_time,
                "location": session.ip_address,
                "browser_agent": session.user_agent,
                "http_accept": session.http_accept,
                "path_info": session.path_info,
                "role": session.role.name if session.role else None,
                "role_id": session.role.id if session.role else None,
                "username": session.username,
                "type": "session",
            }
            result["sessions"].append(session_data)

        # Get active auth tokens
        active_tokens = self.auth_token_set.filter(
            expiry__gt=timezone.now()
        ).select_related("role")

        for token in active_tokens:
            token_data = {
                "digest": token.digest[:8] + "...",  # Show partial digest for security
                "created": timezone.localtime(token.created).strftime(
                    "%Y-%m-%d %H:%M:%S %Z"
                ),
                "created_raw": token.created,
                "expiry": timezone.localtime(token.expiry).strftime(
                    "%Y-%m-%d %H:%M:%S %Z"
                ),
                "expiry_raw": token.expiry,
                "role": token.role.name if token.role else None,
                "role_id": token.role.id if token.role else None,
                "extra_data": token.extra_data,
                "type": "token",
            }
            result["tokens"].append(token_data)

        return result

    def get_last_password_change_date(self):
        """
        Returns the date when the password was last changed

        Returns:
            datetime: Last password change date or None if no password history exists
        """
        last_password = self.oldpasswords_set.all().order_by("-password_date").first()
        if last_password:
            return last_password.password_date
        return None

    def get_password_change_history(self, limit=10):
        """
        Returns the password change history for the user

        Args:
            limit (int): Maximum number of records to return

        Returns:
            list: List of password change dates
        """
        history = []
        old_passwords = self.oldpasswords_set.all().order_by("-password_date")[:limit]

        for old_pwd in old_passwords:
            history.append(
                {
                    # 'changed_at': timezone.localtime(old_pwd.password_date).strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "days_ago": (date.today() - old_pwd.password_date).days
                }
            )

        return history


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
        self.is_used = True
        self.save()


def generate_otp(otp_type, user=None, email=None, phone=None, expiry=300, digits=6):
    try:
        if not user:
            if email:
                user = AppUserModel.objects.filter(email__iexact=email).first()
            elif phone:
                user = AppUserModel.objects.filter(mobile=phone).first()

        min_value = 10 ** (digits - 1)
        max_value = 10**digits - 1

        code = str(secrets.randbelow(max_value - min_value + 1) + min_value)
        expires_at = timezone.now() + timezone.timedelta(seconds=expiry)
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


singatureAlgoChoices = (
    (
        "http://www.w3.org/2000/09/xmldsig#rsa-sha1",
        "http://www.w3.org/2000/09/xmldsig#rsa-sha1",
    ),
    (
        "http://www.w3.org/2000/09/xmldsig#dsa-sha1",
        "http://www.w3.org/2000/09/xmldsig#dsa-sha1",
    ),
    (
        "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
        "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
    ),
    (
        "http://www.w3.org/2001/04/xmldsig-more#rsa-sha384",
        "http://www.w3.org/2001/04/xmldsig-more#rsa-sha384",
    ),
    (
        "http://www.w3.org/2001/04/xmldsig-more#rsa-sha512",
        "http://www.w3.org/2001/04/xmldsig-more#rsa-sha512",
    ),
)

digestAlgorithm = (
    (
        "http://www.w3.org/2000/09/xmldsig#sha1",
        "http://www.w3.org/2000/09/xmldsig#sha1",
    ),
    (
        "http://www.w3.org/2001/04/xmlenc#sha256",
        "http://www.w3.org/2001/04/xmlenc#sha256",
    ),
    (
        "http://www.w3.org/2001/04/xmldsig-more#sha384",
        "http://www.w3.org/2001/04/xmldsig-more#sha384",
    ),
    (
        "http://www.w3.org/2001/04/xmlenc#sha512",
        "http://www.w3.org/2001/04/xmlenc#sha512",
    ),
)


class SAMLModel(models.Model):
    """
    Model to define SAML Configuration for a Company Client
    """

    label = models.CharField("Label for SAML Option", max_length=200)
    is_strict = models.BooleanField(
        verbose_name="If strict is True, then unsigned or unencrypted messages are  rejected if they are expected to be signed/encrypted",
        default=True,
    )
    is_debug_true = models.BooleanField(
        verbose_name="Enable debug mode (outputs errors)", default=False
    )
    sp_entityId = models.URLField(
        verbose_name="Service Provider Entity ID E.g. tenant.zelthy.in/metadata/2/",
    )
    sp_acsURL = models.URLField(
        verbose_name="Service Provider ACS URL E.g. http://tenant.zelthy.in/acs/2/",
    )
    sp_slo = models.URLField(
        verbose_name="Service Provider Single Log Out. Not Implemented Yet", blank=True
    )
    sp_x509cert = models.TextField(
        "Service Provider Public Key x509 Certificate", max_length=2000, blank=True
    )
    sp_privatekey = models.TextField(
        "Service Provider Private Key", max_length=2000, blank=True
    )
    idp_entityId = models.URLField(
        verbose_name="IDP Entity ID . Eg. https://app.onelogin.com/saml/metadata/ace2ffad-66f5-4d43-ae51-bddef851f997",
    )
    idp_sso = models.URLField(
        verbose_name="IDP Single Sing On.  Eg. https://zelthy1.onelogin.com/trust/saml2/http-post/sso/881614",
    )
    idp_slo = models.URLField(
        verbose_name="IDP Single Log On. E.g https://app.onelogin.com/trust/saml2/http-redirect/slo/<onelogin_connector_id>",
        blank=True,
    )
    idp_x509cert = models.TextField(
        "IdP Public Key x509 Certificate",
        max_length=2000,
    )
    security_nameIdEncrypted = models.BooleanField(
        verbose_name="security_nameIdEncrypted. Indicates that the nameID of the <samlp:logoutRequest> sent by this SP will be encrypted",
        default=False,
    )
    security_authnRequestsSigned = models.BooleanField(
        verbose_name="Indicates whether the <samlp:AuthnRequest> messages sent by this SP will be signed",
        default=False,
    )
    security_logoutRequestSigned = models.BooleanField(
        verbose_name="I Indicates whether the <samlp:logoutResponse> messages sent by this SP will be signed",
        default=False,
    )
    security_logoutResponseSigned = models.BooleanField(
        verbose_name="Indicates whether the <samlp:logoutResponse> messages sent by this SP will be signed",
        default=False,
    )
    security_signMetadata = models.BooleanField(
        verbose_name="Sign the Metadata", default=False
    )
    security_wantMessagesSigned = models.BooleanField(
        verbose_name="Indicates a requirement for the <samlp:Response>, <samlp:LogoutRequest> and <samlp:LogoutResponse> elements received by this SP to be signed",
        default=False,
    )
    security_wantAssertionsSigned = models.BooleanField(
        verbose_name="Indicates a requirement for the <saml:Assertion> elements received by this SP to be signed",
        default=False,
    )
    security_wantAssertionsEncrypted = models.BooleanField(
        verbose_name="Indicates a requirement for the <saml:Assertion> elements received by this SP to be encrypted.",
        default=False,
    )
    security_wantNameId = models.BooleanField(
        verbose_name="Indicates a requirement for the NameID element on the SAMLResponse received by this SP to be present.",
        default=True,
    )
    security_wantNameIdEncrypted = models.BooleanField(
        verbose_name="Indicates a requirement for the NameID received by this SP to be encrypted",
        default=False,
    )
    security_wantAttributeStatement = models.BooleanField(
        verbose_name="Indicates a requirement for the AttributeStatement element",
        default=True,
    )
    security_rejectUnsolicitedResponsesWithInResponseTo = models.BooleanField(
        verbose_name=" Rejects SAML responses with a InResponseTo attribute when request_id not provided in the process_response method that later call the response is_valid method with that parameter.",
        default=False,
    )
    security_requestedAuthnContext = models.BooleanField(
        verbose_name="Authentication context", default=True
    )
    security_requestedAuthnContextComparison = models.CharField(
        max_length=10,
        verbose_name="Indicates whether the <samlp:AuthnRequest> messages sent by this SP will be signed",
        default="exact",
    )
    security_signatureAlgorithm = models.CharField(
        max_length=200,
        choices=singatureAlgoChoices,
        default="http://www.w3.org/2000/09/xmldsig#rsa-sha1",
    )
    security_digestAlgorithm = models.CharField(
        max_length=200,
        choices=digestAlgorithm,
        default="http://www.w3.org/2000/09/xmldsig#sha1",
    )
    name_id_format = models.CharField(
        max_length=200,
        default="urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.label

    def get_settings_dict(self):
        result = self.get_basic_settings()
        result["security"] = self.get_security_settings()
        result["contactPerson"] = self.get_contact_settings()
        result["organization"] = self.get_organization()
        return result

    def get_basic_settings(self):
        result = {}
        result["strict"] = self.is_strict
        result["debug"] = self.is_debug_true
        result["sp"] = {}
        result["sp"]["entityId"] = self.sp_entityId
        result["sp"]["assertionConsumerService"] = {
            "url": self.sp_acsURL,
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
        }
        result["sp"]["attributeConsumingService"] = {}
        result["sp"]["singleLogoutService"] = {
            "url": self.sp_slo,
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        }
        result["sp"]["NameIDFormat"] = self.name_id_format
        result["sp"]["x509cert"] = self.sp_x509cert
        result["sp"]["privateKey"] = self.sp_privatekey
        result["idp"] = {}
        result["idp"]["entityId"] = self.idp_entityId
        result["idp"]["singleSignOnService"] = {
            "url": self.idp_sso,
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        }
        result["idp"]["singleLogoutService"] = {
            "url": self.idp_slo,
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        }
        result["idp"]["x509cert"] = self.idp_x509cert
        return result

    def get_security_settings(self):
        result = {}
        result["nameIdEncrypted"] = self.security_nameIdEncrypted
        result["authnRequestsSigned"] = self.security_authnRequestsSigned
        result["logoutRequestSigned"] = self.security_logoutRequestSigned
        result["logoutResponseSigned"] = self.security_logoutResponseSigned
        result["signMetadata"] = self.security_signMetadata
        result["wantMessagesSigned"] = self.security_wantMessagesSigned
        result["wantAssertionsSigned"] = self.security_wantAssertionsSigned
        result["wantAssertionsEncrypted"] = self.security_wantAssertionsEncrypted
        result["wantNameId"] = self.security_wantNameId
        result["wantNameIdEncrypted"] = self.security_wantNameIdEncrypted
        result["wantAttributeStatement"] = self.security_wantAttributeStatement
        result["rejectUnsolicitedResponsesWithInResponseTo"] = (
            self.security_rejectUnsolicitedResponsesWithInResponseTo
        )
        result["requestedAuthnContext"] = self.security_requestedAuthnContext
        result["requestedAuthnContextComparison"] = (
            self.security_requestedAuthnContextComparison
        )
        result["metadataValidUntil"] = None
        result["metadataCacheDuration"] = None
        result["signatureAlgorithm"] = self.security_signatureAlgorithm
        result["digestAlgorithm"] = self.security_digestAlgorithm
        return result

    def get_contact_settings(self):
        result = {}
        result["technical"] = {
            "givenName": "Technical Support",
            "emailAddress": "support@zelthy.com",
        }
        result["support"] = {
            "givenName": "Technical Support",
            "emailAddress": "support@zelthy.com",
        }
        return result

    def get_organization(self):
        result = {
            "en-US": {
                "name": "Healthlane Technologies",
                "displayname": "Zelthy",
                "url": "https://www.zelthy.com",
            }
        }
        return result


class SAMLRequestId(models.Model):
    """
    Stores Request ID of
    """

    request_id = models.CharField("SAML Request ID", max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.request_id


auditlog.register(AppUserModel, m2m_fields={"policies", "roles", "policy_groups"})
auditlog.register(OldPasswords)
auditlog.register(UserRoleModel, m2m_fields={"policy_groups", "policies"})
auditlog.register(AppUserAuthToken)
auditlog.register(OTPCode, exclude_fields=["code"])
