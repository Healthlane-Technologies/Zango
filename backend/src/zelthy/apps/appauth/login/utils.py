import re

from django.conf import settings
from django.contrib.auth import login, REDIRECT_FIELD_NAME
from django.http import Http404
from django.shortcuts import redirect

from formtools.wizard.views import SessionWizardView

from zelthy.apps.appauth.login.base import ZelthyLoginBase


USER_AUTH_BACKEND = "zelthy.apps.appauth.auth_backend.AppUserModelBackend"


class ZelthyLoginView(ZelthyLoginBase, SessionWizardView):

    """
    View for handling the login process
    The login process is composed like a wizard. The first step asks for the
    user's credentials. If the credentials are correct, the wizard prompts user to select a role(from the ones assigned to user).
    Once the user selects the role, it displays Reset password form if the user is logging in for the first time or password is reset from Dynamic Panel
    """

    template_name = ""
    userrolemodel = ""
    redirect_field_name = REDIRECT_FIELD_NAME

    form_list = (
        ("auth", ""),
        ("user_role", ""),
        ("password_reset", ""),
    )

    def has_role_step(self):
        return super(ZelthyLoginView, self).has_role_step()

    def has_password_reset_step(self):
        return super(ZelthyLoginView, self).has_password_reset_step()

    def get_user(self):
        """
        Returns the user authenticated by the AuthenticationForm. Returns False
        if not a valid user; see also issue #65.
        """
        if not self.user_cache:
            form_obj = self.get_form(
                step="auth", data=self.storage.get_step_data("auth")
            )
            self.user_cache = form_obj.user_cache if form_obj.is_valid() else False
        return self.user_cache

    def __init__(self, **kwargs):
        super(ZelthyLoginView, self).__init__(**kwargs)
        self.user_cache = None
        self.device_cache = None

    condition_dict = {
        "user_role": has_role_step,
        "password_reset": has_password_reset_step,
    }

    def done(self, form_list, **kwargs):
        """
        Login the user and redirect to the desired page.
        """
        try:
            form_therapy = [
                form
                for form in form_list
                if isinstance(form, self.form_list.get("user_role"))
            ][0]
            user_role_id = form_therapy.cleaned_data["user_role"]
            user_role = self.get_user().roles.filter(id=user_role_id)[0]
        except Exception as e:
            active_roles = self.get_user().roles.filter(is_active=True)
            if active_roles.count() == 1:
                user_role = active_roles.first()
            elif self.get_user().roles.filter(is_active=True).count() == 1:
                user_role = self.get_user().roles.filter(is_active=True).first()
            else:
                raise Http404(
                    "User does not have any role mapped! Please contact support."
                )
        finally:
            self.request.selected_role_id = user_role.id
        try:
            form_password_reset = [
                form
                for form in form_list
                if isinstance(form, self.form_list.get("password_reset"))
            ][0]
            form_password_reset.save()

        except Exception as e:
            pass

        login(self.request, self.get_user(), backend=USER_AUTH_BACKEND)

        redirect_to = self.request.POST.get(
            self.redirect_field_name, self.request.GET.get(self.redirect_field_name, "")
        )
        if not redirect_to:
            redirect_to = "/app/home/"
        if self.request.is_secure():
            url = "https://" + self.request.META["HTTP_HOST"] + redirect_to
        else:
            url = "http://" + self.request.META["HTTP_HOST"] + redirect_to

        response = redirect(url)

        return response

    def get_form_kwargs(self, step=None):
        """
        AuthenticationTokenForm requires the user kwarg.
        """
        kwargs = {}

        if step == "user_role":
            kwargs.update({"user": self.get_user()})

        if step == "password_reset":
            kwargs.update({"user": self.get_user()})

        return kwargs

    def get_user(self):
        """
        Returns the user authenticated by the AuthenticationForm. Returns False
        if not a valid user; see also issue #65.
        """
        if not self.user_cache:
            data = self.storage.get_step_data("auth")
            form_obj = self.get_form(
                step="auth", data=self.storage.get_step_data("auth")
            )
            self.user_cache = form_obj.is_valid() and form_obj.user_cache
        return self.user_cache

    def get_form_metadata(self, step):
        self.storage.extra_data.setdefault("forms", {})
        return self.storage.extra_data["forms"].get(step, None)


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

