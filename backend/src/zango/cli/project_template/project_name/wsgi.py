"""
WSGI config for testproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from zango.core.monitoring import setup_logging, setup_telemetry

setup_telemetry(add_django_instrumentation=True)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{project_name}}.settings")

application = get_wsgi_application()

setup_logging()