from django.apps import AppConfig


class AuthConfig(AppConfig):
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zelthy.apps.shared.platformauth'

    def ready(self):
        # Import the models here
        from .models import PlatformUserModel
