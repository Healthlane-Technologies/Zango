from django.apps import AppConfig


class AppTemplatesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zango.apps.shared.app_templates"
    # Not "templates": Django and setup.py both give that directory name a
    # meaning of its own, and the label has to be unique across the project.
    label = "app_templates"
    verbose_name = "App Templates"

    def ready(self):
        from django.db.models.signals import post_migrate

        from .seed import seed_bundled_packs

        post_migrate.connect(seed_bundled_packs, sender=self)
