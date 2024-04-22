from django.apps import AppConfig


class AppauthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zcore.apps.appauth"

    def ready(self):
        import zcore.apps.appauth.signals
