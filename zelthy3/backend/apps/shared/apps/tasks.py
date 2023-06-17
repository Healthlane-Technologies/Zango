from celery import shared_task
from backend.core.common_utils import get_next_schema_name
from tenant_schemas.signals import post_schema_sync
from .models import AppModel


@shared_task
def launch_new_app(app_uuid, **kwargs):
    obj = AppModel.objects.get(uuid=app_uuid)
    try:
        obj.create_schema(check_if_exists=True, verbosity=1)
        obj.status = 'deployed'
        obj.save()
    except:
        # We failed creating the tenant, delete what we created and
        # re-raise the exception
        obj.delete(force_drop=True)
        raise
    else:
        post_schema_sync.send(sender=launch_new_app, tenant=obj)
    return
    