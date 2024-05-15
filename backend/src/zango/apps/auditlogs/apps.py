from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuditlogConfig(AppConfig):
    name = "zango.apps.auditlogs"
    verbose_name = _("Audit log")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from zango.apps.auditlogs.registry import auditlog

        auditlog.register_from_settings()

        from zango.apps.auditlogs import models

        models.changes_func = models._changes_func()
