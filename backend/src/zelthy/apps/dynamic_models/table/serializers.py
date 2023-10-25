import pytz

from django.db import models
from django.conf import settings
from rest_framework import serializers
from rest_framework.serializers import SerializerMetaclass

from ..fields import ZForeignKey, ZOneToOneField
from zelthy.core.utils import get_current_request

class StringRelatedMeta(SerializerMetaclass):
    def __new__(cls, name, bases, attrs):
        # Get the Meta class from attrs
        meta = attrs.get('Meta', None)
        # Check if there's a model defined in Meta
        tenant = get_current_request().tenant
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
                    attrs[field.name] = serializers.StringRelatedField()
                if isinstance(field, (models.DateTimeField)):
                    attrs[field.name] = serializers.DateTimeField(format=tenant.datetime_format, default_timezone=pytz.timezone(tenant.timezone))

        return super().__new__(cls, name, bases, attrs)

from zelthy.apps.appauth.models import UserRoleModel

class TestSerializer(serializers.ModelSerializer, metaclass=StringRelatedMeta):
    class Meta:
        model = UserRoleModel