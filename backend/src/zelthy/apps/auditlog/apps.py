from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuditlogConfig(AppConfig):
    name = "zelthy.apps.auditlog"
    verbose_name = _("Audit log")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from zelthy.apps.auditlog.registry import auditlog

        auditlog.register_from_settings()

        from zelthy.apps.auditlog import models

        models.changes_func = models._changes_func()
