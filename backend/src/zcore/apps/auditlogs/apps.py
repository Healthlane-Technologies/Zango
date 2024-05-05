from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuditlogConfig(AppConfig):
    name = "zcore.apps.auditlogs"
    verbose_name = _("Audit log")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from zcore.apps.auditlogs.registry import auditlog

        auditlog.register_from_settings()

        from zcore.apps.auditlogs import models

        models.changes_func = models._changes_func()
