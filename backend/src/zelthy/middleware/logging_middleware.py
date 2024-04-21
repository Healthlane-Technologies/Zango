import uuid
from loguru import logger
from django.http import HttpRequest

class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        
        # Generate a UUID
        log_uuid = uuid.uuid4()

        # Capture schema name and IP address
        schema_name = request.tenant.schema_name
        ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')

        # Use a context manager to bind the context
        with logger.contextualize(schema_name=schema_name, ip_address=ip_address, log_uuid=log_uuid):
            response = self.get_response(request)

        return response
