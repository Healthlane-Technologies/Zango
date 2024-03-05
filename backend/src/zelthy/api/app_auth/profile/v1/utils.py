import re

from django.conf import settings
from django.shortcuts import redirect


class PasswordValidationMixin(object):
    MIN_LENGTH = settings.PASSWORD_MIN_LENGTH
    oldpassword_model = None
    num_specialChar_regex = re.compile(r"[!@#$%^&*()_+-/=~]")
    numeric_regex = re.compile(r"\d")
    uppercase_regex = re.compile(r"[ABCDEFGHIJKLMNOPQRSTUVWXYZ]")
    lowercase_regex = re.compile(r"[abcdefghijklmnopqrstuvwqyz]")

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

    def check_password_length(self, password):
        if len(password) < self.MIN_LENGTH:
            validation = False
            msg = (
                f"The new password must be at least {self.MIN_LENGTH} characters long."
            )

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

    def check_uppercase_char(self, password):
        if not self.uppercase_regex.search(password):
            validation = False
            msg = "The new password must contain at least one upper case character"
        else:
            validation = True
            msg = None
        return {"msg": msg, "validation": validation}

    def check_lowercase_char(self, password):
        if not self.lowercase_regex.search(password):
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

    def check_special_character(self, password):
        msg = ""
        validation = True
        if not self.num_specialChar_regex.search(password):
            validation = False
            msg = "The new password must contain at least one numeric and one special character e.g. ! @ # $ %..."
        if not self.numeric_regex.search(password):
            validation = False
            msg = "The new password must contain at least one numeric and one special character e.g. ! @ # $ %..."
        return {"msg": msg, "validation": validation}

    @staticmethod
    def match_old_password(user, password):
        validation = True
        if user.check_password_validity(password):
            msg = (
                "Sorry, but your new password must not match one of your \
        old passwords from the previous %s days. Please try \
        again!"
                % (settings.PASSWORD_NO_REPEAT_DAYS)
            )
            validation = False
        else:
            msg = ""
        return {"validation": validation, "msg": msg}

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
        if repeat_password:
            if not self.is_password_matching(password, repeat_password).get(
                "validation"
            ):
                return self.is_password_matching(password, repeat_password)

        if old_password:
            if not self.verify_old_password(user, old_password).get("validation"):
                return self.verify_old_password(user, old_password)

        if not self.check_password_length(password).get("validation"):
            return self.check_password_length(password)

        elif not self.is_first_alpha(password).get("validation"):
            return self.is_first_alpha(password)

        elif not self.check_uppercase_char(password).get("validation"):
            return self.check_uppercase_char(password)

        elif not self.check_lowercase_char(password).get("validation"):
            return self.check_lowercase_char(password)

        elif not self.check_special_character(password).get("validation"):
            return self.check_special_character(password)

        elif not self.match_old_password(user, password).get("validation"):
            return self.match_old_password(user, password)

        elif not self.match_password_username(user, password).get("validation"):
            return self.match_password_username(user, password)

        else:
            return {"validation": True, "msg": "Password validations passed"}
