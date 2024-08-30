"""
WSGI config for testproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{project_name}}.settings")


from django.core.wsgi import get_wsgi_application  # noqa: E402

from zango.core.monitoring import setup_telemetry  # noqa: E402


# The telemetry instrumentation library setup needs to run prior to django's setup.
setup_telemetry(add_django_instrumentation=True)

application = get_wsgi_application()

# Our custom loguru logging to should be setup after django has been setup as Django
# will try to override with its own logging setup.
from zango.core.monitoring import setup_logging  # noqa: E402


setup_logging()
