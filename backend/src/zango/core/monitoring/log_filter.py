import logging
import traceback

from loguru import logger

from django.db import connection


class TenantContextFilter(logging.Filter):
    """
    A logging filter that enhances log records with tenant-specific context and
    formats exception tracebacks into a single line.

    This filter adds the following attributes to the log records:
    - `app_name`: the schema name of the current tenant.
    - `domain_url`: the domain URL of the current tenant, if available.
    - `exc_traceback_content`: the formatted exception traceback if an exception is present.
    - `pathname`: the filtered pathname, shortened to start from the 'Zango' directory if present.
    """

    def filter(self, record):
        try:
            record_msg = str(record.msg)
        except Exception as e:
            logger.error(
                f"Exception in str conversion of log record of type: {type(record.msg)}"
            )
            logger.error(f"Exception - {str(e)}")
            record_msg = ""

        record.msg = record_msg
        record.app_name = connection.tenant.schema_name
        record.domain_url = getattr(connection.tenant, "domain_url", "")

        # Formatting logs containing exception traceback into single line
        if record.exc_info:
            ex_type, ex, tb = record.exc_info
            record.exc_traceback_content = traceback.format_tb(tb)
        else:
            record.exc_traceback_content = ""

        splitted_path = str(record.pathname).split("/")
        if "Zango" in splitted_path:
            record.pathname = "/".join(splitted_path[splitted_path.index("Zango") :])
        return True
