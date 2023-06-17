# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import traceback
from django.db import connection
from django.apps import apps
from celery import current_task, shared_task
# from backend.core.loggings import get_file_logger
# logger = get_file_logger()
import logging
logger = logging.getLogger('zelthy')

from .zelthy_exec import zelthy_tasks_safe_exec

@shared_task
def zelthy_custom_task(
        tenant_name, tenant_task_id, *args, **kwargs):    
    client = apps.get_model(
                    app_label='customers', 
                    model_name='client'
                    )
    tenant = client.objects.get(name=tenant_name)
    connection.set_tenant(tenant)
    with connection.cursor() as c:
      task_model = apps.get_model(
                    app_label='customization',
                    model_name='zelthyperiodictasksmodel'
                   )
      obj = task_model.objects.get(id=tenant_task_id)      
      obj.task_ids.append(current_task.request.id)
      obj.save()
      logger.info(
          "Starting execution of Task %s Task ID %s Tenant %s"%(
              obj.name, current_task.request.id, tenant_name)
      )
      _locals = {
                'zelthy_task_handler': None
                }
      zelthy_tasks_safe_exec(
              obj.code, 
              globals(), 
              _locals
              )
      try:
        return _locals["zelthy_task_handler"](**kwargs)
      except:
        logger.error(
          "Error Executing Task %s Task ID %s Tenant %s: %s"%(
              obj.name, current_task.request.id, tenant_name, traceback.format_exc())
                )
