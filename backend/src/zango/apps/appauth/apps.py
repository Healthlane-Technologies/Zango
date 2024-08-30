from django.apps import AppConfig


class AppauthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zango.apps.appauth"

    def ready(self):
        import zango.apps.appauth.signals  # noqa: F401

        pass
