from django.db import models
import sys
from django.utils.translation import gettext_lazy as _

class ZForeignKey(models.ForeignKey):

    def contribute_to_class(self, cls, related):
        super().contribute_to_class(cls, related)
        if all(arg not in sys.argv for arg in ('ws_migrate', 'ws_makemigration')):
            cls._meta.apps.add_models(cls, self.related_model)
            try:
                self.related_model._meta.apps.add_models(self.related_model, cls)
            except:
                pass

            apps = cls._meta.apps            
            apps.do_pending_operations(cls)
            apps.do_pending_operations(self.related_model)
            apps.clear_cache()



class ZOneToOneField(models.OneToOneField):

    def contribute_to_class(self, cls, related):
        super().contribute_to_class(cls, related)
        if all(arg not in sys.argv for arg in ('ws_migrate', 'ws_makemigration')):
            # dont need it if related model is of core
            # try:
            cls._meta.apps.add_models(cls, self.related_model)
            # except:
            #     pass
            try:
                self.related_model._meta.apps.add_models(self.related_model, cls)
            except:
                pass

            apps = cls._meta.apps
            apps.do_pending_operations(cls)
            apps.do_pending_operations(self.related_model)
            apps.clear_cache()


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
        if all(arg not in sys.argv for arg in ('ws_migrate', 'ws_makemigration')):

            apps = cls._meta.apps
            
            model_field = cls._meta.get_field(related)
            through_model = model_field.remote_field.through
            cls._meta.apps.add_models(cls, self.related_model)
            self.related_model._meta.apps.add_models(cls, self.related_model)

            apps.do_pending_operations(self.model)
            apps.do_pending_operations(self.related_model)
            apps.do_pending_operations(through_model)
            apps.clear_cache()  
