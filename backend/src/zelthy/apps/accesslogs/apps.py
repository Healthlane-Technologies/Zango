from django.apps import AppConfig


class CompanyusersAppConfig(AppConfig):

    name = "zelthy.apps.accesslogs"

    def ready(self):
        import zelthy.apps.accesslogs.signals
