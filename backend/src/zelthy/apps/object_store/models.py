from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

import importlib


class ObjectStore(models.Model):
    object_uuid = models.UUIDField(editable=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    @classmethod
    def get_object(cls, object_uuid):
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
                from zelthy.apps.dynamic_models.workspace.base import Workspace
                from django.db import connection

                model_name = obj_store_instance.content_type.model
                wobj = Workspace(connection.tenant, as_systemuser=True)

                content_model = []
                for mod in wobj.get_models():
                    try:
                        _mod = importlib.import_module(mod)
                        for name, obj in vars(_mod).items():
                            if (
                                isinstance(obj, type)
                                and issubclass(obj, models.Model)
                                and obj.__name__.lower() == model_name.lower()
                            ):
                                content_model = [obj]
                                break

                    except:
                        pass

                # If content model found, retrieve the object by primary key
                if content_model:
                    content_model = content_model[0]
                    return content_model.objects.get(pk=obj_store_instance.object_id)

            # If object does not belong to "dynamic_models", return the content object
            return obj_store_instance.content_object
        except cls.DoesNotExist:
            return None
