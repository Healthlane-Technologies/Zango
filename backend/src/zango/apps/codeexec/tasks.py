import json
import traceback

from datetime import datetime as dt

from celery import shared_task

from zango.apps.codeexec.models import ZangoAdminCodeExecutionModel
from zango.apps.shared.tenancy.models import TenantModel
from zango.core.utils import get_mock_request

from .exec import zelthy_codeexec_safe_exec


def is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except Exception:
        return False


def stringify_dict_value(logger_item_value):
    """
    Convert a logger item value to string if they are not.
    """
    if not is_jsonable(logger_item_value):
        try:
            logger_item_value = str(logger_item_value)
        except Exception:
            try:
                logger_item_value = repr(logger_item_value)
            except Exception:
                logger_item_value = "ERROR - Value given here is not json serializable"

    return logger_item_value


def stringify_dict_keys(d):
    """Convert a dict's keys to strings if they are not."""
    for key in d.keys():
        # check inner dict
        if isinstance(d[key], dict):
            value = stringify_dict_keys(d[key])
        else:
            value = d[key]

        # convert nonstring to string if needed
        if not isinstance(key, (str, int)):
            try:
                d[str(key)] = value
            except Exception:
                try:
                    d[repr(key)] = value
                except Exception:
                    # Here we are skipping this dict item as key passed is not json serializable
                    pass

            # delete old key
            del d[key]
    return d


@shared_task
def zelthy_code_execution_task(tenant_name, codeexec_id, *args, **kwargs):
    tenant = TenantModel.objects.get(name=tenant_name)
    from django.db import connection

    connection.set_tenant(tenant)
    connection.request_object = get_mock_request()
    with connection.cursor() as c:
        _obj = ZangoAdminCodeExecutionModel.objects.get(id=codeexec_id)
        _locals = {}
        _locals["zango_codeexec_handler"] = None
        _globals = globals()
        _globals.update(
            {
                "zlogger": {},
                "obj": _obj,  # to support access to artifact
            }
        )
        start_time = str(dt.now().strftime("%d-%m-%Y %H:%M UTC"))
        task_info = {
            "start_time": start_time,
            "end_time": "NA",
            "code": _obj.code,
            "status": "STAGED",
        }
        execution_history = _obj.execution_history
        execution_history.append(task_info)
        _obj.execution_history = execution_history
        _obj.save()
        try:
            zelthy_codeexec_safe_exec(_obj.code, _globals, _locals)
            _locals["zango_codeexec_handler"]()
            end_time = str(dt.now().strftime("%d-%m-%Y %H:%M UTC"))
            execution_history = _obj.execution_history
            # stringify keys
            _globals["zlogger"] = stringify_dict_keys(_globals["zlogger"])

            for logger_item_key, logger_item_value in _globals["zlogger"].items():
                # stringify value
                logger_item_value = stringify_dict_value(logger_item_value)
                # _globals["zlogger"].update({
                #     logger_item_key: mask_log_record(str(logger_item_value))
                # })

            execution_history[-1].update(
                {
                    "end_time": end_time,
                    "logger": _globals["zlogger"],
                    "status": "COMPLETED",
                }
            )
            _obj.execution_history = execution_history
            _obj.save()

        except Exception:
            end_time = str(dt.now().strftime("%d-%m-%Y %H:%M UTC"))
            execution_history = _obj.execution_history
            execution_history[-1].update(
                {
                    "end_time": end_time,
                    "logger": _globals["zlogger"],
                    "traceback": traceback.format_exc(),
                    "status": "FAILED",
                }
            )
            _obj.execution_history = execution_history
            _obj.save()
        return
