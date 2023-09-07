import sys
from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import pre_save
from .signals import set_created_modified_by


class DynamicModelsConfig(AppConfig):

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zelthy.apps.dynamic_models'
    

    def ready(self):
        # thanks to Baserow for this hack
        import zelthy.apps.dynamic_models.signals
        original_register_model = self.apps.register_model
        def register_model(app_label, model):
            if 'ws_makemigration' in sys.argv or getattr(settings, "TEST_MIGRATION_RUNNING", False):
                original_register_model(app_label, model)
            else:
                pre_save.connect(set_created_modified_by, sender=model)
                self.apps.do_pending_operations(model)
                self.apps.clear_cache()
        self.apps.register_model = register_model


