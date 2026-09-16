from django.apps import AppConfig


class PlatformSettingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zango.apps.shared.platform_settings"
    label = "platform_settings"
    verbose_name = "Platform Settings"
