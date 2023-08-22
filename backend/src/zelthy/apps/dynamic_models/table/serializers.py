

from django.db import models
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
            for field in model._meta.fields:
                # Check if the field is a relational field
                if isinstance(field, (models.ForeignKey, models.OneToOneField, ZForeignKey, ZOneToOneField)):
                    # Use StringRelatedField for this field
                    attrs[field.name] = serializers.StringRelatedField()

        return super().__new__(cls, name, bases, attrs)

from zelthy3.backend.apps.tenants.appauth.models import UserRoleModel

class TestSerializer(serializers.ModelSerializer, metaclass=StringRelatedMeta):
    class Meta:
        model = UserRoleModel