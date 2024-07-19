import logging
from loguru import logger
import traceback
from django.db import connection

class TenantContextFilter(logging.Filter):
    """Adds schema 

    Args:
        logging (_type_): _description_
    """
    def filter(self, record):
        try:
            record_msg = str(record.msg)
        except Exception as e:
            logger.error(f"Exception in str conversion of log record of type: {type(record.msg)}")
            logger.error(f"Exception - {str(e)}")
            record_msg = ""

        record.msg = record_msg
        record.app_name = connection.tenant.schema_name
        record.domain_url = getattr(connection.tenant, 'domain_url', '')

        # Formatting logs containing exception traceback into single line
        if record.exc_info:
            ex_type, ex, tb = record.exc_info
            record.exc_traceback_content = traceback.format_tb(tb)
        else:
            record.exc_traceback_content = ""
        
        splitted_path = str(record.pathname).split('/')
        if 'Zango' in splitted_path:
            record.pathname = "/".join(splitted_path[splitted_path.index('Zango'):])
        return True