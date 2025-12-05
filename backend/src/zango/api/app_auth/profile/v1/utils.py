import re

from django.conf import settings

from zango.apps.appauth.models import AppUserModel
from zango.core.utils import get_auth_priority


class PasswordValidationMixin:
    MIN_LENGTH = settings.PASSWORD_MIN_LENGTH
    oldpassword_model = None
    num_specialChar_regex = re.compile(r"[!@#$%^&*()_+-/=~]")
    numeric_regex = re.compile(r"\d")
    uppercase_regex = re.compile(r"[ABCDEFGHIJKLMNOPQRSTUVWXYZ]")
    lowercase_regex = re.compile(r"[abcdefghijklmnopqrstuvwqyz]")

    def get_password_policy(self, user=None):
        """
        Fetch password policy from database using get_auth_priority
        """
        policy = get_auth_priority(policy="password_policy", user=user)
        return policy

    @staticmethod
    def is_password_matching(password, password2):
        """
        Checks if both passwords are equal
        """
        validation = password == password2
        if not validation:
            msg = "The two passwords didn't match!"
        else:
            msg = None
        return {"validation": validation, "msg": msg}

    def check_password_length(self, password, user=None):
        policy = self.get_password_policy(user)
        if isinstance(policy, dict):
            min_length = policy.get("min_length", self.MIN_LENGTH) or self.MIN_LENGTH
        else:
            min_length = self.MIN_LENGTH

        if len(password) < min_length:
            validation = False
            msg = f"The new password must be at least {min_length} characters long."

        else:
            validation = True
            msg = None
        return {"validation": validation, "msg": msg}

    @staticmethod
    def is_first_alpha(password):
        """
        First character must be alphabet
        """
        validation = password[0].isalpha()
        if not validation:
            msg = "The first letter of your password must be an alphabet!"
        else:
            msg = None
        return {"validation": validation, "msg": msg}

    def check_uppercase_char(self, password, user=None):
        policy = self.get_password_policy(user)
        require_uppercase = (
            policy.get("require_uppercase", True) if isinstance(policy, dict) else True
        )

        if require_uppercase and not self.uppercase_regex.search(password):
            validation = False
            msg = "The new password must contain at least one upper case character"
        else:
            validation = True
            msg = None
        return {"msg": msg, "validation": validation}

    def check_lowercase_char(self, password, user=None):
        policy = self.get_password_policy(user)
        require_lowercase = (
            policy.get("require_lowercase", True) if isinstance(policy, dict) else True
        )

        if require_lowercase and not self.lowercase_regex.search(password):
            validation = False
            msg = "The new password must contain at least one lower case character"
        else:
            validation = True
            msg = None
        return {"msg": msg, "validation": validation}

    def verify_old_password(self, user, old_password):
        if not user.check_password(old_password):
            msg = "Current password does not match. Please try again!"
            validation = False
        else:
            msg = ""
            validation = True
        return {"validation": validation, "msg": msg}

    def check_special_character(self, password, user=None):
        policy = self.get_password_policy(user)
        require_special_chars = (
            policy.get("require_special_chars", True)
            if isinstance(policy, dict)
            else True
        )
        require_numbers = (
            policy.get("require_numbers", True) if isinstance(policy, dict) else True
        )

        msg = ""
        validation = True

        if require_special_chars and not self.num_specialChar_regex.search(password):
            validation = False
            msg = "The new password must contain at least one special character e.g. ! @ # $ %..."

        if require_numbers and not self.numeric_regex.search(password):
            validation = False
            if msg:
                msg = "The new password must contain at least one numeric and one special character e.g. ! @ # $ %..."
            else:
                msg = "The new password must contain at least one numeric character"

        return {"msg": msg, "validation": validation}

    @staticmethod
    def match_old_password(user, password):
        res = user.check_password_validity(password)
        return {"validation": res["validation"], "msg": res["message"]}

    @staticmethod
    def match_password_username(user, password):
        validation = True
        msg = None
        if password.lower() == user.email.lower():
            validation = False
        if not validation:
            msg = "Your password must be different from your username."
        return {"msg": msg, "validation": validation}

    def run_all_validations(
        self, user, password, repeat_password=None, old_password=None
    ):
        if not isinstance(user, AppUserModel):
            user = AppUserModel.objects.get(id=user.id)

        if repeat_password:
            if not self.is_password_matching(password, repeat_password).get(
                "validation"
            ):
                return self.is_password_matching(password, repeat_password)

        if old_password:
            if not self.verify_old_password(user, old_password).get("validation"):
                return self.verify_old_password(user, old_password)

        if not self.check_password_length(password, user).get("validation"):
            return self.check_password_length(password, user)

        elif not self.is_first_alpha(password).get("validation"):
            return self.is_first_alpha(password)

        elif not self.check_uppercase_char(password, user).get("validation"):
            return self.check_uppercase_char(password, user)

        elif not self.check_lowercase_char(password, user).get("validation"):
            return self.check_lowercase_char(password, user)

        elif not self.check_special_character(password, user).get("validation"):
            return self.check_special_character(password, user)

        elif not self.match_old_password(user, password).get("validation"):
            return self.match_old_password(user, password)

        elif not self.match_password_username(user, password).get("validation"):
            return self.match_password_username(user, password)

        else:
            return {"validation": True, "msg": "Password validations passed"}
