import os
import uuid
import logging
import traceback
from django.views.generic import View
from django.http import JsonResponse
from pathlib import Path
from django.db import connection


class ZelthyLogFilter(logging.Filter):

    def filter(self, record):
        try:
            record_msg = str(record.msg)
        except Exception as e:
            print(e)
            print("Exception in str conversion of log record of type: ", type(record.msg))
            record_msg = "In Exception"

        record.msg = record_msg
        record.uuid = str(uuid.uuid4())
        record.schema_name = connection.tenant.schema_name
        record.domain_url = getattr(connection.tenant, 'domain_url', '')

        # Formatting logs containing exception traceback into single line
        if record.exc_info:
            ex_type, ex, tb = record.exc_info
            record.exc_traceback_content = traceback.format_tb(tb)
        else:
            record.exc_traceback_content = ""
        
        splitted_path = str(record.pathname).split('/')
        if 'zelthy3' in splitted_path:
            record.pathname = "/".join(splitted_path[splitted_path.index('zelthy3'):])
        return True
