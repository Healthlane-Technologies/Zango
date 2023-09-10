from django.apps import AppConfig


class AppauthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zelthy.apps.appauth'

    def ready(self):
        import zelthy.apps.appauth.signals
