from zango.core.utils import get_current_request


def set_created_modified_by(sender, instance, **kwargs):
    req = get_current_request()
    if req and req.user and req.user.__class__.__name__ == "AppUserModel":
        user = req.user
    else:
        user = None
    if not instance.pk:
        instance.created_by = user
    else:
        instance.modified_by = user
    return


def create_object_store_entry(sender, instance, created, **kwargs):
    if created:
        from django.contrib.contenttypes.models import ContentType

        from zango.apps.object_store.models import ObjectStore

        content_type = ContentType.objects.get_for_model(sender)
        ObjectStore.objects.create(
            object_uuid=instance.object_uuid,
            content_type=content_type,
            object_id=instance.pk,
            content_object=instance,
        )
