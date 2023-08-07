from django.db import models
import sys

class ZForeignKey(models.ForeignKey):

    def contribute_to_class(self, cls, related):
        super().contribute_to_class(cls, related)
        if all(arg not in sys.argv for arg in ('zmigrate', 'zmakemigrations')):    
            cls._meta.apps.add_models(cls, self.related_model)
            try:
                self.related_model._meta.apps.add_models(self.related_model, cls)
            except:
                pass

            apps = cls._meta.apps
            apps.do_pending_operations(cls)
            apps.do_pending_operations(self.related_model)
            apps.clear_cache()



class ZOneToOneField(models.OneToOneField):

    def contribute_to_class(self, cls, related):
        super().contribute_to_class(cls, related)
        if all(arg not in sys.argv for arg in ('zmigrate', 'zmakemigrations')):
            # dont need it if related model is of core
            # try:
            cls._meta.apps.add_models(cls, self.related_model)
            # except:
            #     pass
            try:
                self.related_model._meta.apps.add_models(self.related_model, cls)
            except:
                pass

            apps = cls._meta.apps
            apps.do_pending_operations(cls)
            apps.do_pending_operations(self.related_model)
            apps.clear_cache()


class ZManyToManyField(models.ManyToManyField):
    
    
    # def m2m_field_name(self):
    #     print("m2m_field_name being called..")

    # def m2m_reverse_field_name(self):
    #     print("m2m_reverse_field_name being called..")

    # def m2m_field_name(self):
    #     return 'address_1'
    
    # def m2m_reverse_field_name(self):
    # def contribute_to_related_class(self, cls, related):
    #     print("Inside contribute to related class")
    #     super().contribute_to_related_class(cls, related)

    # def contribute_to_class(self, cls, related):
    #     print("here", self, cls, related, type(related))
    #     super().contribute_to_class(cls, related)
    #     model_field = cls._meta.get_field(related)
    #     through_model = model_field.remote_field.through
    #     print("model_field--> ", model_field)
    #     print("through_model-->", through_model)
        

    #     cls._meta.apps.add_models(cls, self.related_model)
    #     self.related_model._meta.apps.add_models(self.related_model, cls)
        
    #     apps = cls._meta.apps
    #     app_config = apps.get_app_config('dynamic_models')
    #     setattr(app_config, 'models', {'patient': cls, 'address': self.related_model, 'patient_address_1': through_model})
    #     print(app_config)
    #     print(app_config.models)
    #     apps.do_pending_operations(cls)
    #     apps.do_pending_operations(self.related_model)
    #     apps.do_pending_operations(through_model)
    #     apps.clear_cache()
    pass