import uuid
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class ObjectStore(models.Model):
    object_uuid = models.UUIDField(editable=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    @classmethod
    def get_object_by_uuid(cls, object_uuid):
        """
        A class method that retrieves the corresponding object from the object store by its UUID.

        Parameters:
            cls (class): The class itself.
            object_uuid (str): The UUID of the object to retrieve.

        Returns:
            obj: The retrieved object if found, None otherwise.
        """
        try:
            # Retrieve the object store instance by UUID
            obj_store_instance = cls.objects.get(object_uuid=object_uuid)

            # Check if the object belongs to "dynamic_models" app
            if obj_store_instance.content_type.app_label == "dynamic_models":
                from zelthy.apps.dynamic_models.models import DynamicModelBase

                model_name = obj_store_instance.content_type.model

                # Get the content model matching the model name
                apps = DynamicModelBase._meta.apps
                content_model = [
                    _model
                    for _model in apps.get_models()
                    if _model.__name__.lower() == model_name.lower()
                ]

                # If content model found, retrieve the object by primary key
                if content_model:
                    content_model = content_model[0]
                    return content_model.objects.get(pk=obj_store_instance.object_id)

            # If object does not belong to "dynamic_models", return the content object
            return obj_store_instance.content_object
        except cls.DoesNotExist:
            return None
