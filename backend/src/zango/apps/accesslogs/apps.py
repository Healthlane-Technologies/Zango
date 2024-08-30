from django.apps import AppConfig


class AccesslogsAppConfig(AppConfig):
    name = "zango.apps.accesslogs"

    def ready(self):
        import zango.apps.accesslogs.signals  # noqa: F401

        pass
