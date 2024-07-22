import sys
import os
import logging


from .utils import otel_is_enabled
from .telemetry import setup_log_exporting


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
        "<level>{message}</level>\n"
    )
    return loguru_format


def setup_logging():

    from loguru import logger
    from django.conf import settings
    
    # Removes the default format 
    logger.remove()
    
    # Add our customized format that adds the tenant context and removes unnecessary initial 
    # path for the tenants
    if settings.ENV == 'dev':        
        logger.add(
            sys.stderr, format=_get_loguru_format, level='INFO'
        )
    else:
        logger.add(
            'log/zango.log', 
            format=_get_loguru_format, 
            level='INFO', 
            rotation="5 MB",
            retention="1 month"
        )
    logger.info("Logger setup.")
    if otel_is_enabled():
        setup_log_exporting(logger)