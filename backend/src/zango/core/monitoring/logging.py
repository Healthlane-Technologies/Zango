import sys
import os

def _get_tenant_name():
    from django.db import connection
    try:
        tenant_name = connection.tenant.name
    except Exception as e:        
        tenant_name = 'FakeTenant'
    return tenant_name

def _get_tenant_filename(original_name):
    if original_name.startswith("pluginbase"):
        result = f"workspaces.{_get_tenant_name()}.{'.'.join(original_name.split('.')[3:])}"
    else:
        result = original_name        
    return result
        
    
def _get_loguru_format(record):
    file_name = _get_tenant_filename(record['name'])
    
    loguru_format = (
        f"<magenta>{os.getpid()}|</magenta>"
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>|"
        "<level>{level}</level>|"
        f"<cyan>{file_name}</cyan>:"
        "<cyan>{function}</cyan>:"
        "<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    return loguru_format

def setup_logging():

    from loguru import logger
    
    # A slightly customized default loguru format which includes the process id.
    logger.remove()
    # Replace it with our format, loguru recommends sending application logs to stderr.
    logger.add(
        sys.stderr, format=_get_loguru_format, level='INFO'
    )
    logger.info("Logger setup.")