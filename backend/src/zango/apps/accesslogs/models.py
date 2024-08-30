from axes.models import AccessBase

from django.db import models

from zango.apps.appauth.models import AppUserModel, UserRoleModel


class AppAccessLog(AccessBase):
    user = models.ForeignKey(AppUserModel, null=True, on_delete=models.CASCADE)
    role = models.ForeignKey(
        UserRoleModel, null=True, blank=True, on_delete=models.CASCADE
    )
    attempt_type = models.CharField(max_length=20, null=True)
    is_login_successful = models.BooleanField(default=False)
    session_expired_at = models.DateTimeField(null=True, blank=True)

    class Meta(AccessBase.Meta):
        app_label = "accesslogs"
