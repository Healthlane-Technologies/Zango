from django.apps import AppConfig


class AgentModePlatformConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zango.apps.shared.agent_mode"
    # Distinct label: zango.apps.agent_mode (tenant) would otherwise collide,
    # since Django derives the label from the last path component.
    label = "agent_mode_platform"
    verbose_name = "Agent Mode (Platform)"
