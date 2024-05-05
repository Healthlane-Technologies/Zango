import uuid
from django.db import connection


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_next_schema_name():
    """
    TODO: Add check for the improbable case of schema name already existing in db
    """
    return "zc_" + "".join(str(uuid.uuid4()).split("-")[:2])


def set_app_schema_path(f):
    """
    check possibility of decorating all methods of the class in one go:
    https://stackoverflow.com/questions/6307761/how-to-decorate-all-functions-of-a-class-without-typing-it-over-and-over-for-eac
    """

    def wrapper(*args, **kwargs):
        from django.apps import apps
        from django_tenants.utils import schema_context

        model = apps.get_model("tenancy", "TenantModel")
        app = model.objects.get(uuid=kwargs.get("app_uuid"))
        with schema_context(app.schema_name):
            return f(*args, **kwargs)

    return wrapper
