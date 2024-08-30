from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zango.apps.shared.platformauth"

    def ready(self):
        # Import the models here
        from .models import PlatformUserModel  # noqa: F401

        pass
