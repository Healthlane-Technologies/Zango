from django.apps import AppConfig


class AccesslogsAppConfig(AppConfig):

    name = "zelthy.apps.accesslogs"

    def ready(self):
        import zelthy.apps.accesslogs.signals
