import os
import uuid
import logging
import traceback
from django.views.generic import View
from django.http import JsonResponse
from pathlib import Path
from django.db import connection


# Add the middleware for capturing IP address
class IPAddressMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logging.request = request
        response = self.get_response(request)
        return response

class CustomFilter(logging.Filter):

    def filter(self, record):
        try:
            record_msg = str(record.msg)
        except Exception as e:
            print(e)
            print("Exception in str conversion of log record of type: ", type(record.msg))
            record_msg = "In Exception"

       # Extract client IP address from the request object in logging context
        request = getattr(logging, 'request', None)
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                record.remote_addr = x_forwarded_for.split(',')[0]
            else:
                record.remote_addr = request.META.get('REMOTE_ADDR')
        else:
            record.remote_addr = "N/A"  # Default value if request object is not available
        
        

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
