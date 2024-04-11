from django.db import models
from axes.models import AccessBase

from ..appauth.models import AppUserModel, UserRoleModel


class AppUserAccessLogs(AccessBase):

    user = models.ForeignKey(AppUserModel, null=True, on_delete=models.CASCADE)
    role = models.ForeignKey(
        UserRoleModel, null=True, blank=True, on_delete=models.CASCADE
    )
    attempt_type = models.CharField(max_length=20, null=True)
    is_login_successful = models.BooleanField(default=False)
    session_expired_at = models.DateTimeField(null=True, blank=True)
