from rest_framework import serializers
from rest_framework.renderers import JSONRenderer

from .serializers import StringRelatedMeta
from .column import Column

class ModelTable:

    """
        Supports table creation for a model. The model is specified in the Meta class. 
        The fields of the model are specified in the fields attribute. For including all 
        the fields of the model use __all__. 
        Custom fields can also be specified directly as class attributes as Column Object. 
    """
    pagination = 10
    fields = []
    custom_fields = []
    field_map = {
        'BigAutoField': {
            'type': 'integer',
            'searchable': True,
            'sortable': True,
        },
        'AutoField': {
            'type': 'integer',
            'searchable': True,
            'sortable': True,
        },
        'CharField': {
            'type': 'string',
            'searchable': True,
            'sortable': True,
        },
        'IntegerField': {
            'type': 'integer',
            'searchable': True,
            'sortable': True,
        },
        'FloatField': {
            'type': 'float',
            'searchable': True,
            'sortable': True,
        },
        'BooleanField': {
            'type': 'boolean',
            'searchable': True,
            'sortable': True,
        },
        'DateField': {
            'type': 'date',
            'searchable': True,
            'sortable': True,
        },
        'DateTimeField': {
            'type': 'datetime',
            'searchable': True,
            'sortable': True,
        },
        'EmailField': {
            'type': 'email',
            'searchable': True,
            'sortable': True,
        },
        'FileField': {
            'type': 'file',
            'searchable': False,
            'sortable': False,
        },
        'ImageField': {
            'type': 'image',
            'searchable': False,
            'sortable': False,
        },
        'DecimalField': {
            'type': 'decimal',
            'searchable': True,
            'sortable': True,
        },
        'TextField': {
            'type': 'string',
            'searchable': True,
            'sortable': False,
        },
        'UUIDField': {
            'type': 'uuid',
            'searchable': True,
            'sortable': True,
        },
        'ZOneToOneField':{
            'type': 'string',
            'searchable': True,
            'sortable': True
        },
        'ZForeignKey':{
            'type': 'string',
            'searchable': True,
            'sortable': True
        },
        'JSONField':{
            'type': 'json',
            'searchable': False,
            'sortable': False
        }
    }
   

    def __init__(self):
        self.model = self.Meta.model
        self.serializer_class = getattr(self.Meta, 'serializer_class', None)

        if self.Meta.fields == '__all__':
            self.fields = [f.name for f in self.model._meta.fields]
        else:
            self.fields = self.Meta.fields
            # for field in self.fields: TODO
            #     if field not in self.model._meta.fields:
            #         raise ValueError(f"field {field} not a field in model {self.model}")


    def get_table_metadata(self) -> list[dict]:
        """
            Returns the metadata of the table to help build the table UI,
            excluding the data rows.
    
            Args:
                self (Table): The current instance of the Table class.                
            Returns:
                metadata (list[dict]): A list of dictionaries representing the metadata
                    of the table.
        """
        columns = []
        for field in self.model._meta.fields:
            if field.name in self.fields:
                column = self.field_map[field.__class__.__name__]                
                column.update(name=field.name, choices=field.choices)
                columns.append(column)
        metadata = {
            "pagination": self.pagination,
            "columns": columns,
        }
        return metadata
    
    def get_serializer(self):
        if self.serializer_class:
            return self.serializer_class
        
        class Meta:
            model = self.model
            fields = self.Meta.fields

        serializer_name = f'{self.model.__class__.__name__}Serializer'
        serializer_class = StringRelatedMeta(serializer_name, (serializers.ModelSerializer,), {'Meta': Meta})
        return serializer_class

    def get_data(self, request) -> list[dict]:
        objects = self.model.objects.all()
        serializer = self.get_serializer()
        # data = JSONRenderer().render(serializer(objects, many=True).data)
        data = serializer(objects, many=True).data
        return data
                

        



