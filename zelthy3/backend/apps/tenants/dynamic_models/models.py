from django.db import models
from django.apps import apps

from django.core.exceptions import FieldDoesNotExist as DjangoFieldDoesNotExist
from types import MethodType

def patch_meta_get_field(_meta):
    original_get_field = _meta.get_field

    def get_field(self, field_name, *args, **kwargs):
        try:
            return original_get_field(field_name, *args, **kwargs)
        except DjangoFieldDoesNotExist as exc:
            print("Inside DjangoFieldDoesNotExist")
            try:
                field_object = self.model.get_field_object(
                    field_name, include_trash=True
                )

            except ValueError:
                raise exc

            field_type = field_object["type"]
            # logger.debug(
            #     "Lazy load missing {} of type {} for table {}",
            #     field_name,
            #     field_type.type,
            #     self.model.pk,
            # )
            field_type.after_model_generation(
                field_object["field"], self.model, field_object["name"]
            )
            return original_get_field(field_name, *args, **kwargs)

    _meta.get_field = MethodType(get_field, _meta)


class RegisterOnceModeMeta(type(models.Model)):
    pass

    def __new__(mcs, name, bases, attrs):
        if apps.ready:
            try:
                model = apps.get_model('dynamic_models', name)
                return model # Model already registered. Won't register twice
            except LookupError:
                model = super().__new__(mcs, name, bases, attrs)
                # patch_meta_get_field(model._meta)
                return model
        model = super().__new__(mcs, name, bases, attrs) 
        return model
        
class DefaultAppsProxy:
    """
    A proxy class to the default apps registry.
    This class is needed to make our dynamic models available in the
    options when the relation tree is built.
    """

    def __init__(self):
        self._extra_models = []

    def add_models(self, *dynamic_models):
        """
        Adds a model to the default apps registry.
        """
        self._extra_models.extend(dynamic_models)

    def get_models(self, *args, **kwargs):
        return apps.get_models(*args, **kwargs) + self._extra_models

    def __getattr__(self, attr):
        return getattr(apps, attr)
        
class DynamicModelBase(models.Model, metaclass=RegisterOnceModeMeta):

    class Meta:
        app_label = 'dynamic_models'
        apps = DefaultAppsProxy()
        abstract = True