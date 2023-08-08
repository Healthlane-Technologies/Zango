from django.db import models
import sys

class ZForeignKey(models.ForeignKey):

    def contribute_to_class(self, cls, related):
        super().contribute_to_class(cls, related)
        if all(arg not in sys.argv for arg in ('zmigrate', 'zmakemigrations')):    
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
        if all(arg not in sys.argv for arg in ('zmigrate', 'zmakemigrations')):
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


class ZManyToManyField(models.ManyToManyField):
    
    def m2m_field_name(self):
        """
        Function that can be curried to provide the source accessor or DB
        column name for the m2m table.
        """
        attr = "name"
        cache_attr = "_m2m_%s_cache" % attr
        related = self.remote_field

        if hasattr(self, cache_attr):
            return getattr(self, cache_attr)
        if self.remote_field.through_fields is not None:
            link_field_name = self.remote_field.through_fields[0]
        else:
            link_field_name = None
        
        for f in self.remote_field.through._meta.fields:
            if (
                f.is_relation
                and f.remote_field.model == related.related_model
                and (link_field_name is None or link_field_name == f.name)
            ):
                setattr(self, cache_attr, getattr(f, attr))
                return getattr(self, cache_attr)
    

    def m2m_reverse_field_name(self):
        """
        Function that can be curried to provide the related accessor or DB
        column name for the m2m table.
        """
        attr = "name"
        cache_attr = "_m2m_reverse_%s_cache" % attr
        related = self.remote_field
        
        if hasattr(self, cache_attr):
            return getattr(self, cache_attr)
        
        found = False
        if self.remote_field.through_fields is not None:
            link_field_name = self.remote_field.through_fields[1]
        else:
            link_field_name = None
        for f in self.remote_field.through._meta.fields:
            if f.is_relation and f.remote_field.model == related.model:
                if link_field_name is None and related.related_model == related.model:
                    # If this is an m2m-intermediate to self,
                    # the first foreign key you find will be
                    # the source column. Keep searching for
                    # the second foreign key.
                    if found:
                        setattr(self, cache_attr, getattr(f, attr))
                        break
                    else:
                        found = True
                elif link_field_name is None or link_field_name == f.name:
                    setattr(self, cache_attr, getattr(f, attr))
                    break
        return getattr(self, cache_attr)