import sys

from django.conf import settings
from django.db import models
from django.db.models.signals import class_prepared


# from django.utils.translation import gettext_lazy as _


# Argv guards that disable the runtime apps fix-up. Migration / fixture
# commands run their own model-resolution machinery and don't need (or
# want) this codepath.
_RUNTIME_GUARD_ARGS = (
    "ws_migrate",
    "ws_makemigration",
    "export_fixture",
    "import_fixture",
    "update-apps",
)


def _runtime_active() -> bool:
    """True when we're in a normal request-serving / worker context —
    i.e. not running one of the migration / fixture management commands
    listed in `_RUNTIME_GUARD_ARGS`, and not inside a TEST_MIGRATION_RUNNING
    block."""
    return all(arg not in sys.argv for arg in _RUNTIME_GUARD_ARGS) and not getattr(
        settings, "TEST_MIGRATION_RUNNING", False
    )


def _defer_pending_operations(cls, *related_models):
    """Schedule `apps.do_pending_operations` calls to fire after `cls`
    is fully prepared.

    Calling `apps.do_pending_operations(cls)` from inside a field's
    `contribute_to_class` fires queued pending operations against `cls`
    BEFORE `cls._meta.concrete_model` is set by `_prepare()`. Pending
    operations typically end up calling
    `setattr(cls._meta.concrete_model, accessor_name, descriptor)` —
    `concrete_model` is `None` at that point, so `setattr(None, ...)`
    raises `AttributeError` and breaks the class definition.

    Django emits `class_prepared` for each model after `Options._prepare`
    has set `concrete_model`. By attaching the pending-op resolution to
    that signal we run it at the first moment it's safe. The receiver
    disconnects itself after firing so we don't accumulate dead handlers
    on the global signal.

    `weak=False` keeps the inner closure alive between `connect` and
    the imminent `send` — without it Python would garbage-collect the
    closure as soon as `contribute_to_class` returns.
    """
    if not related_models:
        related_models = ()

    def _resolve_pending(sender, **kwargs):
        try:
            apps = sender._meta.apps
            apps.do_pending_operations(sender)
            for related in related_models:
                if related is None:
                    continue
                try:
                    apps.do_pending_operations(related)
                except Exception:
                    # related may still be a string ref or otherwise
                    # unresolvable; skip rather than break sender's prep.
                    pass
            apps.clear_cache()
        finally:
            class_prepared.disconnect(_resolve_pending, sender=sender)

    class_prepared.connect(_resolve_pending, sender=cls, weak=False)


class ZForeignKey(models.ForeignKey):
    def contribute_to_class(self, cls, related):
        super().contribute_to_class(cls, related)
        if _runtime_active():
            cls._meta.apps.add_models(cls, self.related_model)
            try:
                self.related_model._meta.apps.add_models(self.related_model, cls)
            except Exception:
                pass
            _defer_pending_operations(cls, self.related_model)


class ZOneToOneField(models.OneToOneField):
    def contribute_to_class(self, cls, related):
        super().contribute_to_class(cls, related)
        if _runtime_active():
            # dont need it if related model is of core
            cls._meta.apps.add_models(cls, self.related_model)
            try:
                self.related_model._meta.apps.add_models(self.related_model, cls)
            except Exception:
                pass
            _defer_pending_operations(cls, self.related_model)


# from django.db.models.utils import make_model_tuple
# from ..models import DefaultAppsProxy, RegisterOnceModeMeta

# def zcreate_many_to_many_intermediary_model(field, klass):

#     from django.db import models
#     from django.db.models.fields.related import resolve_relation, lazy_related_operation

#     def set_managed(model, related, through):
#         through._meta.managed = model._meta.managed or related._meta.managed

#     to_model = resolve_relation(klass, field.remote_field.model)
#     name = "%s_%s" % (klass._meta.object_name, field.name)
#     lazy_related_operation(set_managed, klass, to_model, name)

#     to = make_model_tuple(to_model)[1]
#     from_ = klass._meta.model_name
#     if to == from_:
#         to = "to_%s" % to
#         from_ = "from_%s" % from_

#     meta = type(
#         "Meta",
#         (),
#         {
#             "db_table": field._get_m2m_db_table(klass._meta),
#             "auto_created": klass,
#             "app_label": klass._meta.app_label,
#             "db_tablespace": klass._meta.db_tablespace,
#             "unique_together": (from_, to),
#             "verbose_name": _("%(from)s-%(to)s relationship")
#             % {"from": from_, "to": to},
#             "verbose_name_plural": _("%(from)s-%(to)s relationships")
#             % {"from": from_, "to": to},
#             "apps": DefaultAppsProxy()
#             # "apps": field.model._meta.apps,
#         },
#     )
#     # Construct and return the new class.
#     return RegisterOnceModeMeta(
#         name,
#         (models.Model,),
#         {
#             "Meta": meta,
#             "__module__": klass.__module__,
#             from_: ZForeignKey(
#                 klass,
#                 related_name="%s+" % name,
#                 db_tablespace=field.db_tablespace,
#                 db_constraint=field.remote_field.db_constraint,
#                 on_delete=models.CASCADE,
#             ),
#             to: ZForeignKey(
#                 to_model,
#                 related_name="%s+" % name,
#                 db_tablespace=field.db_tablespace,
#                 db_constraint=field.remote_field.db_constraint,
#                 on_delete=models.CASCADE,
#             ),
#         },
#     )


class ZManyToManyField(models.ManyToManyField):
    def contribute_to_class(self, cls, related):
        super().contribute_to_class(cls, related)
        if all(arg not in sys.argv for arg in ("ws_migrate", "ws_makemigration")):
            model_field = cls._meta.get_field(related)
            through_model = model_field.remote_field.through
            cls._meta.apps.add_models(cls, self.related_model)
            self.related_model._meta.apps.add_models(cls, self.related_model)
            _defer_pending_operations(cls, self.related_model, through_model)
