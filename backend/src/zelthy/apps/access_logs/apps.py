from django.apps import AppConfig


class AccesslogsAppConfig(AppConfig):

    name = "zelthy.apps.access_logs"

    def ready(self):
        import zelthy.apps.access_logs.signals
