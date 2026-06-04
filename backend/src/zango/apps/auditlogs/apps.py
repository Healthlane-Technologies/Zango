from django.apps import AppConfig
from django.db.models.signals import class_prepared
from django.utils.translation import gettext_lazy as _


def _auto_register_workspace_model(sender, **kwargs):
    """Register any workspace model with auditlog at the moment its class
    statement finishes executing.

    Background:
    ``Workspace.load_models()`` is the only place that calls
    ``auditlog.register(model)`` for workspace models, and it walks the
    set of models produced by **pluginbase's** loader. Each loader run
    creates fresh class objects in its own namespace; ``signal.connect``
    pins the receiver to that specific class object.

    A direct import — ``from workspaces.<app>.<package>.models import X``
    in a Django shell, in code execution snippets, in management
    commands — bypasses pluginbase and produces a *different* class
    object. The audit registration never ran against it, so saves on
    instances of that class silently skip the audit log.

    Hooking Django's ``class_prepared`` signal closes the gap: every
    DynamicModelBase subclass gets registered exactly once per class
    object, the moment that class object is constructed, regardless of
    which loader (pluginbase, stdlib import, importlib) produced it.
    """
    # Lazy imports — this runs during Django boot before the apps
    # registry is fully populated. DynamicModelBase is a Django model
    # itself; importing it eagerly at module load would create a cycle
    # via AppConfig.ready().
    from zango.apps.auditlogs.registry import auditlog
    from zango.apps.dynamic_models.models import DynamicModelBase

    if sender is DynamicModelBase:
        return
    try:
        if not issubclass(sender, DynamicModelBase):
            return
    except TypeError:
        # `sender` wasn't a class (defensive — shouldn't happen for
        # class_prepared, but guards against unexpected emitters).
        return

    if auditlog.contains(sender):
        return

    meta = getattr(sender, "DynamicModelMeta", None)
    if meta is not None and getattr(meta, "exclude_audit_log", False):
        return

    excluded_fields = (
        getattr(meta, "exclude_audit_log_fields", None) if meta is not None else None
    )
    if excluded_fields:
        auditlog.register(sender, exclude_fields=excluded_fields)
    else:
        auditlog.register(sender)


class AuditlogConfig(AppConfig):
    name = "zango.apps.auditlogs"
    verbose_name = _("Audit log")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from zango.apps.auditlogs.registry import auditlog

        auditlog.register_from_settings()

        from zango.apps.auditlogs import models

        models.changes_func = models._changes_func()

        # Auto-register every workspace model regardless of import path
        # — fixes audit-log gaps in Django shell, code execution
        # snippets, and any other entry point that bypasses
        # ``Workspace.load_models()``. See `_auto_register_workspace_model`
        # docstring for details.
        class_prepared.connect(
            _auto_register_workspace_model,
            dispatch_uid="zango.auditlogs.auto_register_workspace_model",
        )
