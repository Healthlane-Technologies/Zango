import sys
from django.apps import AppConfig
from django.conf import settings



class DynamicModelsConfig(AppConfig):

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'zelthy3.backend.apps.tenants.dynamic_models'
    

    def ready(self):
        # thanks to Baserow for this hack
        original_register_model = self.apps.register_model
        def register_model(app_label, model):
            if 'zmakemigrations' in sys.argv or getattr(settings, "TEST_MIGRATION_RUNNING", False):
                original_register_model(app_label, model)
            else:
                self.apps.do_pending_operations(model)
                self.apps.clear_cache()
        self.apps.register_model = register_model


