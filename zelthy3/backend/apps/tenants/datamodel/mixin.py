from typing import Any
from django.db import models, connection
from django.db.models.base import ModelBase
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.postgresql.base import DatabaseWrapper
from django.db import connections
from copy import deepcopy
# from phonenumber_field.modelfields import PhoneNumberField
from .fields import DataModelFileField, DataModelForeignKey
import ast
import json
import logging
import importlib

logger = logging.getLogger("zelthy")


FIELDS_MAPPER = {
    'IntegerField': models.IntegerField,
    'CharField': models.CharField,
    'BooleanField': models.BooleanField,
    'DateField': models.DateField,
    'DateTimeField': models.DateTimeField,
    'FloatField': models.FloatField,
    'TextField': models.TextField,
    'OneToOneField': models.OneToOneField,
    'DataModelForeignKey': models.ForeignKey,
    'ManyToManyField': models.ManyToManyField,
    'EmailField': models.EmailField,
    # 'PhoneNumberField': PhoneNumberField,
    'URLField': models.URLField,
    'FileField': DataModelFileField
}

def repr(x):
    model_specs = json.loads(str(x.model_specs))
    if model_specs.get("field_str_repr"):
        model_repr = model_specs["field_str_repr"]
        if x.id:
            return "{} ({})".format(model_repr, x.id + 10000)
        return model_repr
    if x.id:
        return "{} ({})".format(str(x.__class__), x.id + 10000)
    return str(x.__class__)

class CustomModelBase(ModelBase):

    def __init__(self, *args, **kwargs):
        super(CustomModelBase, self).__init__(
            *args,
            **kwargs
        )
    
    def __str__(self):
        model_specs =  json.loads(str(self.model_specs))
        if model_specs.get("field_str_repr"):
            return model_specs["field_str_repr"]
        return self.__name__

class DynamicModelMixin(object):

    def _get_model(self, field_specs, model_specs):
        # Define a dictionary to map field types to their corresponding Django model fields
        _specs = deepcopy(field_specs)
        # Define a dictionary to store the model fields
        model_fields = {}
        print(_specs)
        for field in _specs:
            field_type = field['field_type']
            field_attributes = field['attrs']
            field_name = field.pop("field_name")
            if "_unique" in field_attributes:
                field_attributes.pop("_unique")
            if "is_relation" in field_attributes:
                field_attributes.pop("is_relation")
            if "creation_counter" in field_attributes:
                field_attributes.pop("creation_counter")
            if field_attributes.get('verbose_name'):
                verbose_name = field['attributes'].pop('verbose_name')
            else:
                verbose_name = field_name
            
            if field_type in ['DataModelForeignKey', 'OneToOneField', 'ManyToManyField']:
                if field_type in ['DataModelForeignKey', 'OneToOneField']:
                    field_attributes['on_delete'] = models.PROTECT

                related_model = field_attributes.pop('related_model')
                print(related_model, field_attributes)
                model_field = FIELDS_MAPPER[field_type](related_model, **field_attributes)
            if field_type == 'FileField':
                model_field = FIELDS_MAPPER[field_type](verbose_name, **field_attributes)
            if field_type == 'CharField' and field_attributes.get('choices', False):
                field_attributes['choices'] = ast.literal_eval(field_attributes['choices'].encode("utf-8"))
                model_field = FIELDS_MAPPER[field_type](verbose_name, **field_attributes)
            else:
                model_field = FIELDS_MAPPER[field_type](verbose_name, **field_attributes)
                

            # Get the corresponding Django model field and add it to the model_fields dictionary
            model_fields[field_name] = model_field
        
        updated_model_fields = { key: value for key, value in model_fields.items()}
        updated_model_fields["__module__"] = __name__
        updated_model_fields["model_specs"] = model_specs
        updated_model_fields["__str__"] = repr
        
        # Create a dynamic model class using the models.Model class as a base
        dynamic_model = CustomModelBase(str(self.label), (models.Model,), updated_model_fields)
        return dynamic_model

    def _get_model_alt(self):
        usr = importlib.import_module("zelthy3.zelthy_apps.Tenant.ddm.user").TenantUser

        rol = importlib.import_module("zelthy3.zelthy_apps.Tenant.ddm.user").TenantRole
        # rol._meta.app_label = 'zelthy3.backend.apps.tenants.datamodel'
        # rol._meta.db_table = "datamodel_tenantrole"
        return rol, usr

    def generate_sql_from_specs(self, field_specs, model_name):
        statements = []
        """
        this requires GRANT USAGE ON SCHEMA information_schema TO your_user;
        """
        table_name = "datamodel_"+self.label
        schema_name = connection.tenant.schema_name
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('%s.%s')"%(schema_name, table_name))
            result = cursor.fetchone()
            table_sql_lines = []
            
            if not result[0]:
                primary_key = "id SERIAL PRIMARY KEY"
                table_sql_lines = ["CREATE TABLE {} (".format(table_name), " {}, ".format(primary_key)]
            
            field_sql = []
            for field in field_specs:
                field_type = field["field_type"]
                attrs = field["attrs"]

                if field_type == "IntegerField":
                    if attrs.get('unique', False) == True:
                        sql = "%s INTEGER UNIQUE %s"%(field["field_name"],
                                                '' if attrs.get('null') else 'NOT NULL')
                    else:
                        sql = "%s INTEGER %s DEFAULT %s" % (field["field_name"], 
                                                        'NULL' if attrs.get('null') else 'NOT NULL',
                                                        attrs.get('default') if attrs.get('default') is not None else 'NULL')
                elif field_type == "CharField":
                    # if attrs.get("choices"):
                    #     sql = "%s VARCHAR(%s) %s CHECK (%s IN %s)" %(field["field_name"],
                    #                             attrs['max_length'],
                    #                             'NULL' if attrs.get('null') else 'NOT NULL',
                    #                             field["field_name"],
                    #                             tuple([x.encode('utf-8') for x in attrs.get("choices")]),
                    #                             )
                    if attrs.get('unique'):
                        sql = "%s VARCHAR(%s) UNIQUE %s"%(field["field_name"],
                                                attrs['max_length'],
                                                '' if attrs.get('null') else 'NOT NULL')
                    if attrs.get("default"):
                        sql = "%s VARCHAR(%s) %s DEFAULT '%s'" % (field["field_name"], attrs['max_length'],
                                                            'NULL' if attrs.get('null') else 'NOT NULL',
                                                            attrs.get('default') if attrs.get('default') is not None else 'NULL')
                    else:
                        sql = "%s VARCHAR(%s) %s" % (field["field_name"], attrs['max_length'],
                                                            'NULL' if attrs.get('null') else 'NOT NULL')
                elif field_type == "BooleanField":
                    sql = "%s BOOLEAN %s DEFAULT %s" % (field["field_name"],'NULL' if attrs.get('null') else 'NOT NULL', attrs.get('default'))
                elif field_type == "DateField":
                    if attrs.get('unique', False) == True:
                        sql = "%s DATE UNIQUE %s" % (field["field_name"],
                                                    'NULL' if attrs.get('null') else 'NOT NULL')
                    else:
                        sql = "%s DATE %s DEFAULT %s" % (field["field_name"],
                                                    'NULL' if attrs.get('null') else 'NOT NULL',
                                                    attrs.get('default') if attrs.get('default') is not None else 'NULL')
                elif field_type == "DateTimeField":
                    if attrs.get('unique', False) == True:
                        sql = "%s TIMESTAMP UNIQUE %s" % (field["field_name"],
                                                    'NULL' if attrs.get('null') else 'NOT NULL')
                    if attrs.get("default") is not None:
                        sql = "%s TIMESTAMP %s DEFAULT '%s'" % (field["field_name"],
                                                            'NULL' if attrs.get('null') else 'NOT NULL',
                                                            attrs.get("default") if attrs.get('default') is not None else 'NULL')
                    else:
                        sql = "%s TIMESTAMP %s" % (field["field_name"],
                                                                'NULL' if attrs.get('null') else 'NOT NULL')
                elif field_type == "FloatField":
                    if attrs.get('unique', False) == True:
                        sql = "%s FLOAT UNIQUE %s"%(field["field_name"],
                                                '' if attrs.get('null') else 'NOT NULL')
                    if attrs.get('default'):
                        sql = "%s FLOAT DEFAULT %s" % (field["field_name"], attrs.get('default'))
                    else:
                        sql = "%s FLOAT %s" % (field["field_name"], 'NULL' if attrs.get('null') else 'NOT NULL')
                elif field_type == "TextField":
                    if attrs.get('unique'):
                        sql = "%s TEXT UNIQUE %s"%(field["field_name"],
                                                '' if attrs.get('null') else 'NOT NULL')
                    if attrs.get("default"):
                        sql = "%s TEXT %s DEFAULT '%s'" % (field["field_name"],
                                        'NULL' if attrs.get('null') else 'NOT NULL',
                                        attrs.get('default') if attrs.get('default') is not None else 'NULL')
                    else:
                        sql = "%s TEXT %s" % (field["field_name"],
                                                    'NULL' if attrs.get('null') else 'NOT NULL')
                elif field_type == "DataModelOneToOneField":
                    related_model = attrs['related_model']
                    sql = "%s_id INTEGER UNIQUE %s REFERENCES %s(id)" % (attrs["field_name"],
                                                                        'NULL' if attrs.get('null', None) else 'NOT NULL',
                                                                        related_model)
                elif field_type == "DataModelForeignKey":
                    related_model = attrs['related_model']
                    sql = "%s_id INTEGER %s REFERENCES %s(id)" % (attrs["field_name"],
                                                                    'NULL' if attrs.get('null', None) else 'NOT NULL',
                                                                    related_model)
                elif field_type == "EmailField":
                    if attrs.get("unique"):
                        sql = "%s VARCHAR UNIQUE %s" % (field["field_name"], 'NULL' if attrs.get('null', None) else 'NOT NULL')
                    if attrs.get("default"):
                        sql = "%s VARCHAR DEFAULT %s" % (field["field_name"], attrs.get("default"))
                    else:
                        sql = "%s VARCHAR %s" % (field["field_name"], 'NULL' if attrs.get('null', None) else 'NOT NULL')
                elif field_type == "PhoneNumberField":
                    if attrs.get("unique"):
                        sql = "%s VARCHAR UNIQUE %s" % (field["field_name"], 'NULL' if attrs.get('null', None) else 'NOT NULL')
                    if attrs.get("default"):
                        sql = "%s VARCHAR DEFAULT %s" % (field["field_name"], attrs.get("default"))
                    else:
                        sql = "%s VARCHAR %s" % (field["field_name"], 'NULL' if attrs.get('null', None) else 'NOT NULL')
                elif field_type == "URLField":
                    if attrs.get("default"):
                        sql = "%s TEXT DEFAULT %s" %(field["field_name"], )
                    sql = "%s TEXT %s" %(field["field_name"], 'UNIQUE' if attrs.get('unique', None) else '')
                elif field_type == "DataModelManyToManyField":
                    related_model = attrs['related_model']
                    query = '''
                        CREATE TABLE datamodel_{model_name}_{field} (
                            id SERIAL PRIMARY KEY,
                            {model_name}_id INTEGER NOT NULL REFERENCES datamodel_{model_name}(id) ON DELETE {on_delete},
                            tenantuser_id INTEGER NOT NULL REFERENCES {related_model}(id) ON DELETE {on_delete}
                        );
                        '''.format(
                            field=attrs["field_name"],
                            model_name=model_name,
                            related_model=related_model,
                            on_delete=attrs.get("on_delete", "CASCADE")
                    )
                    statements.append(query)
                elif field_type == "FileField":
                    sql = "%s VARCHAR %s" % (field["field_name"], 'NULL' if attrs.get('null', None) else 'NOT NULL')
                else:
                    continue
                if field_type != "DataModelManyToManyField":
                    field_sql.append(sql)

            
            if table_sql_lines:
                table_sql_lines.extend(["\t{}, ".format(sql) for sql in field_sql])
                table_sql_lines[-1] = table_sql_lines[-1].rstrip().rstrip(",")  # Remove the trailing comma
                table_sql_lines.append(");")
            else:
                table_sql_lines = ["ALTER TABLE {} ".format(table_name)]
                table_sql_lines.extend(["\n ADD COLUMN {},".format(sql) for sql in field_sql])
                table_sql_lines[-1] = table_sql_lines[-1].rstrip().rstrip(",")  # Remove the trailing comma
                table_sql_lines.append(";")

            table_sql = "".join(table_sql_lines)
            statements.insert(0, table_sql)
            
            return statements
            
    