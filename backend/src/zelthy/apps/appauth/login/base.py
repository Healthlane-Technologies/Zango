from django.conf import settings


class ZelthyLoginBase(object):
    login_steps = [
        "auth",
        "user_role",
        "password_reset",
    ]

    def allow_login(self, request):
        return True

    def get_user(self):
        """
        returns User based on credential check of CompanyUser
        """
        raise NotImplementedError()

    def has_role_step(self):
        """
        If only one role then don't show
        show if 0 or >1 roles
        """
        user = self.get_user()
        if user:
            return user.has_role_step(self.request)
        return False

    def has_auth_step(self):
        """
        Later can implement that we dont need username password authentication
        """
        return True

    def has_password_reset_step(self):
        """
        Checks if password reset is required
        """
        no_of_days = settings.PASSWORD_RESET_DAYS
        user = self.get_user()
        if user and user.has_password_reset_step(self.request, days=no_of_days):
            return True
        return False
