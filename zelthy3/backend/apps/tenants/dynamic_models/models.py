from django.db import models
from django.apps import apps



class RegisterOnceModeMeta(type(models.Model)):

    def __new__(mcs, name, bases, attrs):
        print("Inside Metaclass", name)
        if apps.ready:
            try:
                return apps.get_model('dynamic_models', name) # Model already registered. Won't register twice
            except LookupError:
                return super().__new__(mcs, name, bases, attrs)
        return super().__new__(mcs, name, bases, attrs)
        

        
class DynamicModelBase(models.Model, metaclass=RegisterOnceModeMeta):

    class Meta:
        app_label = 'dynamic_models'
        abstract = True