from django.core.management.base import BaseCommand, CommandError, CommandParser
import os
import importlib
import sys
import inspect
from zelthy3.backend.apps.tenants.datamodel.models import DynamicTable
import traceback
from django.db import connection
from django.db import models
from django.db.models.base import ModelBase
from django_tenants.utils import get_tenant_model
from zelthy3.backend.apps.tenants.datamodel.models import SimpleMixim
from django.apps import apps
from django.db.models.fields import NOT_PROVIDED

"""
    
"""

field_map = {
    "CharField": {
        "name": ("NR", None),
        "verbose_name": ("NR", None),
        "max_length": ("R", None),
        "blank": ("NR", False),
        "null": ("NR", False),
        "default": ("NR", NOT_PROVIDED),
        "choices": ("NR", None),
        "unique": ("NR", False)
    },
    "IntegerField": {
        "name": ("NR", None),
        "verbose_name": ("NR", None),
        "blank": ("NR", False),
        "null": ("NR", False),
        "default": ("NR", NOT_PROVIDED),
        "unique": ("NR", False)
    },
    "FloatField": {
        "name": ("NR", None),
        "verbose_name": ("NR", None),
        "max_length": ("R", None),
        "blank": ("NR", False),
        "null": ("NR", False),
        "default": ("NR", NOT_PROVIDED),
        "unique": ("NR", False)
    }
}

rel_field_map = {
    "one_to_one": "DataModelOneToOneField",
    "foreign_key": "DataModelForeignKey",
    "many_to_many": "DataModelManyToManyField"
}

class Command(BaseCommand):
    help = "Performs the migration operation for the datamodels in the project"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("tenant_name", help="Name of the tenant")
        parser.add_argument("module_name", help="Name of the module containing the model")

    def handle(self, *args, **options):
        tenant_name = options["tenant_name"]
        tenant_model = get_tenant_model()
        env = tenant_model.objects.get(name=tenant_name)
        connection.set_tenant(env)
        with connection.cursor() as c:
            sys.path.append(os.getcwd())
            
            modules = os.listdir(f"./zelthy_apps/{tenant_name}")
            if options["module_name"]:
                modules = [options["module_name"]]
            
            for module in modules:

                ddms = {}
            
                with open(f"./zelthy_apps/{tenant_name}/{module}/models.py") as f:
                    content = f.read()
                    exec(content, globals())
                    for name, obj in globals().items():
                        if type(obj) == ModelBase and name not in ["ModelBase", "DynamicTable", "SimpleMixim"]:
                            obj.__module__ = f"zelthy_apps.{tenant_name}.{module}.models"
                            ddms[name] = obj

                for desc, dataclass in ddms.items():
                    field_specs = []
                    for field_name, specs in vars(dataclass).items():
                        if any(rel_field in field_name for rel_field in rel_field_map.keys()):
                            attrs = {}
                            field_type = rel_field_map[field_name[:-2]]
                            for field, val in vars(specs).items():
                                attrs[field] = val
                            field_spec = {
                                "field_name": field_name,
                                "attrs": attrs,
                                "field_type": field_type
                            }
                            field_specs.append(field_spec)
                        else:
                            attrs = {}
                            try:
                                vars(specs)
                            except Exception:
                                continue
                            if vars(specs).get("field"):
                                field_type = str(vars(specs)["field"].__class__)
                                field_type = field_type[field_type.rfind(".") + 1:field_type.rfind("'")]
                                if field_type not in field_map.keys():
                                    continue
                                attrs = {}
                                for field, val in vars(vars(specs)["field"]).items():
                                    # if field != "_unique" or field != 'is_relation':
                                    #     if type(val) in [ int, bool, float, str, dict, None]:
                                    #         attrs[field] = val
                                    if field in field_map[field_type].keys():
                                        if type(val) in [ int, bool, float, str, dict, None]:
                                            if field_map[field_type][field][1] != val:
                                                attrs[field] = val
                                field_spec = {
                                    "field_name": field_name,
                                    "attrs": attrs,
                                    "field_type": field_type
                                }
                                field_specs.append(field_spec)
                    model_name = "".join(desc)
                    print(field_specs)
                    obj = None
                    
                    try:
                        obj = DynamicTable.objects.get(label=desc)
                    except:
                        obj = DynamicTable(label=desc, description="", field_specs={})
                        obj.full_clean()
                        obj.save()
                    
                    obj.update_model_schema(field_specs, desc)
                    obj.migrate_schema()
