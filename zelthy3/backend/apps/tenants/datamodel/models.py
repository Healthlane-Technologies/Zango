import uuid
import time
import re
from django.db import models, connection
from django.core.exceptions import ValidationError
from zelthy3.backend.core.model_mixins import FullAuditMixin
from django.db.models import JSONField
from django.apps import apps
import traceback

from .mixin import DynamicModelMixin
import logging

logger = logging.getLogger("zelthy")

"""
we will use metaclass to create model.py equivalent for a particular ZelthyObjectTypes model obj

"""

def validate_name(name):
    if not re.match(r'^[a-zA-Z]+$', name):
        raise ValidationError('Name cannot contains special characters, whitespace or numbers')


# Create your models here.
class DynamicTable(FullAuditMixin, DynamicModelMixin):
    
    allowed_types = ['IntegerField', 'CharField', 'BooleanField', 'DateField', 'DateTimeField', 'FloatField', \
        'TextField',  'OneToOneField', 'ForeignKey', 'ManyToManyField', 'FileField']    

    label = models.CharField(
                    "Label",
                    max_length=100,
                    unique=True,
                    validators=[validate_name]
                    )
    field_specs = JSONField(
                    null=True,
                    blank=True
                )
    description = models.TextField(
        "model_description",
        blank=True,
        default="",
        max_length=300
    )

    def __str__(self):
        return self.label
    
    def update_model_schema(self, field_specs, model_name):
        try:
            if self.field_specs:
                for obj in self.field_specs["versions"]:
                    if obj['is_migrated'] == False:
                        return False, "Failed. There is a non-migrated version. Please migrate before making any changes to schema."
            
            for field in field_specs:
                field_names = set()
                if field["field_name"] not in field_names:
                    field_names.add(field["field_name"])
                else:
                    return False, "Duplicate Field"
                
            existing_field_names = []
            for f in self.field_specs.get("versions", []):
                for field_spec in f["specs"]:
                   existing_field_names.append(field_spec["field_name"]) 
            
            field_specs = [f for f in field_specs if f["field_name"] not in existing_field_names]
            data = self.field_specs or {"versions": []}
            migration_required = False
            if field_specs:
                new_version = 1 if not self.field_specs else max([v["version"] for v in self.field_specs["versions"]]) + 1
                obj = {
                    "version": new_version,
                    "specs": field_specs,
                    "sql": self.generate_sql_from_specs(field_specs, model_name),
                    "is_migrated": False,
                    "timestamp": round(time.time())
                }
                data["versions"].append(obj)
                migration_required = True
            self.field_specs = data
            self.save()
            return True, "Successfully updated", migration_required
        except Exception as e:
            logger.exception(e)
            return False, traceback.print_exc(), False

    def migrate_schema(self):
        """
        Apply all unmigrated schema chenages
        """
        unmigrated_objects = []
        if self.field_specs:         
            for obj in self.field_specs["versions"]:
                if not obj["is_migrated"]:
                    unmigrated_objects.append(obj)
        if not unmigrated_objects:
            return False, "No unmigrated schema changes exist"
        else:
            if len(unmigrated_objects) > 1:
                return False, "More than one unmigrated schema changes exist."
            else:
                with connection.cursor() as cursor:
                    try:
                        for statement in unmigrated_objects[0]["sql"]:
                            logger.info("statement %s", statement)
                            cursor.execute(statement)
                        field_specs = self.field_specs
                        for f in field_specs["versions"]:
                            if not f["is_migrated"]:
                                f["is_migrated"] = True
                        self.field_specs = field_specs
                        self.save()
                        return True, "Migrated successfully!"
                    except Exception as e:
                        logger.exception(e)
                        return False, "Encountered an error %s"%(e)

    @classmethod
    def load_model(cls, label):
        obj = cls.objects.filter(label=label).first()
        if obj and obj.field_specs:
            try:
                all_field_specs = []
                for field_spec in obj.field_specs["versions"]:
                    all_field_specs.extend(field_spec["specs"])
                
                if all_field_specs:
                    return obj._get_model(all_field_specs, obj.field_specs.get("model_specs", {}))
            except Exception as e:
                return traceback.format_exc()
        return None
    
    @classmethod
    def load_model_alt(cls, label):
        obj = cls.objects.filter(label=label).first()
        if obj and obj.field_specs:
            try:
                return obj._get_model_alt()
            except Exception as e:
                traceback.print_exc()
                return None
        return None

class SimpleMixim(models.Model):
    
    class Meta:
        app_label = 'zelthy3.backend.apps.tenants.datamodel'
        abstract = True