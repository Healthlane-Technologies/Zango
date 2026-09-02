from django.apps import AppConfig


class AppsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zango.apps.shared.tenancy"

    def ready(self):
        import zango.apps.shared.tenancy.signals  # noqa: F401
