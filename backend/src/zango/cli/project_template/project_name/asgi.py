"""
ASGI config for testproject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from zango.core.monitoring import setup_telemetry


# The telemetry instrumentation library setup needs to run prior to django's setup.
setup_telemetry(add_django_instrumentation=True)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{project_name}}.settings")

application = get_asgi_application()

# Our custom loguru logging to should be setup after django has been setup as Django
# will try to override with its own logging setup.
from zango.core.monitoring import setup_logging  # noqa: E402


setup_logging()
