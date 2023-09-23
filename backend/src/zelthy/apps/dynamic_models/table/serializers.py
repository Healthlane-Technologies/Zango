from django.db import models
from django.conf import settings
from rest_framework import serializers
from rest_framework.serializers import SerializerMetaclass

from ..fields import ZForeignKey, ZOneToOneField

class StringRelatedMeta(SerializerMetaclass):
    def __new__(cls, name, bases, attrs):
        # Get the Meta class from attrs
        meta = attrs.get('Meta', None)
        # Check if there's a model defined in Meta
        if meta and hasattr(meta, 'model'):
            model = meta.model
            # Iterate through the model's fields
            # fields = attrs['Meta'].__dict__.get('fields')
            # if fields == '__all__':
            #     fields = model._meta
            for field in model._meta.fields:
                # Check if the field is a relational field
                if isinstance(field, (models.ForeignKey, models.OneToOneField, ZForeignKey, ZOneToOneField)):
                    # Use StringRelatedField for this field
                    pass
                    # attrs[field.name] = serializers.StringRelatedField()
                # if isinstance(field, (models.DateTimeField)):
                #     attrs[field.name] = serializers.DateTimeField(format='Y-m-d H:i:s', default_timezone=None)
                    # attrs[field.name] = serializers.DateTimeField(format=settings.DATETIME_FORMAT, default_timezone=None)

        return super().__new__(cls, name, bases, attrs)

from zelthy.apps.appauth.models import UserRoleModel

class TestSerializer(serializers.ModelSerializer, metaclass=StringRelatedMeta):
    class Meta:
        model = UserRoleModel