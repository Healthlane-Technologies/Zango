import copy

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
        'ZFileField': {
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
        'ForeignKey':{
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


class ModelCol:
    
    model_field = None
    display_as = None
    _type = None
    searchable = None
    sortable = None
    choices = None

    def __init__(self, *args, **kwargs):
        self.display_as = kwargs.get('display_as', None)
        self._type = kwargs.get('type', None)
        self.searchable = kwargs.get('searchable', None)
        self.sortable = kwargs.get('sortable', None)
        self.choices = kwargs.get('choices', None)
        self.user_roles = kwargs.get('user_roles', [])

    def update_model_field(self, field):
        self.model_field = field
    
    def get_col_metadata(self):
        metadata = copy.deepcopy(field_map[self.model_field.__class__.__name__])               
        metadata.update(name=self.model_field.name, choices=self.model_field.choices)
        if self.display_as:
            metadata.update(display_name=self.display_as)
        if self._type:
            metadata.update(type=self._type)
        if self.searchable is not None:
            metadata.update(searchable=self.searchable)
        if self.sortable is not None:
            metadata.update(sortable=self.sortable)
        if self.choices:
            metadata.update(choices=self.choices)
        return metadata

class StringCol:
    
    def __init__(self, *args, **kwargs):
        self.searchable = kwargs.get('searchable', False)
        self.sortable = kwargs.get('sortable', False)
        self.user_roles = kwargs.get('user_roles', [])
    
    def update_model_name(self, name):
        self.name = name
        return
    
    def get_col_metadata(self):
        metadata = {
            'type': 'string',
            'name': self.name,
            'searchable': self.searchable,
            'sortable': self.sortable
        }
        return metadata

    
class NumericCol:

    def __init__(self, *args, **kwargs):
        pass

class SelectCol:

    def __init__(self, *args, **kwargs):
        pass
