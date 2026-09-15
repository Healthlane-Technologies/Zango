from django.apps import AppConfig


class AgentModeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zango.apps.agent_mode"
    label = "agent_mode"
    verbose_name = "Agent Mode"
