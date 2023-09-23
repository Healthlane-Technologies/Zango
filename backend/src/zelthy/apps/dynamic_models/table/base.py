import copy
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from django.db.models import Q
from django.db import models
from zelthy.core.utils import get_current_role
from .serializers import StringRelatedMeta
from .column import ModelCol, StringCol, NumericCol, SelectCol

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

    def __init__(self):
        self.user_role = get_current_role()
        self.model = self.Meta.model
        self.serializer_class = getattr(self.Meta, 'serializer_class', None)
        self.native_fields = [f.name for f in self.model._meta.fields]
        explicit_cols = []
        explicit_col_names = []
        for attr_name, attr_value in type(self).__dict__.items():
            try:
                if attr_value.__class__ == ModelCol:
                    attr_value.update_model_field(self.model._meta.get_field(attr_name))
                elif attr_value.__class__ in [StringCol, NumericCol, SelectCol]:
                    attr_value.update_model_name(attr_name)
                if attr_value.__class__ in [ModelCol, StringCol, NumericCol, SelectCol]:                    
                    if (not attr_value.user_roles) or \
                            (attr_value.user_roles and self.user_role.name in attr_value.user_roles):
                        explicit_cols.append((attr_name, attr_value))
                        explicit_col_names.append(attr_name)
            except Exception as e:
                print(e)
        if self.Meta.fields == '__all__':
            # print()
            for f in self.model._meta.fields:
                if f.name not in explicit_col_names:
                    col = ModelCol()
                    col.update_model_field(f)
                    explicit_cols.append((f.name, col))

        else:
            self._fields = self.Meta.fields
            for f in self._fields:
                if f not in explicit_col_names:
                    col = ModelCol()
                    field = self.model._meta.get_field(f)
                    col.update_model_field(field)
                    explicit_cols.append((f, col))
        
        self._fields = explicit_cols
        self.actions_metadata = self.get_actions_metadata()

    def get_actions_metadata(self):
        actions = {"row":[], "table": []}

        for row in self.row_actions:
            roles = row.get("roles", [])
            if (not roles) or \
                            (roles and self.user_role.name in roles):
                actions["row"].append(row)
        for action in self.table_actions:
            roles = action.get("roles", [])
            if (not roles) or \
                            (roles and self.user_role.name in roles):
                actions["table"].append(action)
        return actions



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
        columns = [f[1].get_col_metadata() for f in self._fields]
        metadata = {
            "pagination": self.pagination,
            "columns": columns,
            "row_selector": self.Meta.row_selector,
            "actions": self.actions_metadata
            # "actions": self.get_actions_metadata()

        }
        return metadata
    
    
    def get_serializer(self):
        if self.serializer_class:
            return self.serializer_class
        
        class Meta:
            model = self.model
            if self.Meta.fields == '__all__':
                fields = [f.name for f in self.model._meta.fields]
            else:
                fields = self.Meta.fields
            fields = list(set(fields + ['created_at', 'modified_at', 'created_by', 'modified_by']))

        

        serializer_name = f'{self.model.__class__.__name__}Serializer'
        serializer_class = StringRelatedMeta(serializer_name, (serializers.ModelSerializer,), {'Meta': Meta})
        return serializer_class
    
    def post_process_data(self, data):
        result = []
        columns = self.get_columns()
        i = 0
        for row in data:
            obj, serialized = row['obj'], row['serialized']
            new_row = {}
            for col in columns:
                col_getval = getattr(self, f'{col}_getval', None)
                if col_getval:
                    new_row[col] = col_getval(obj)
                else:
                    new_row[col] = serialized[col]
            result.append(new_row)
        return result
    
    def get_columns(self):
        columns = self.get_table_metadata()["columns"]
        return [c["name"] for c in columns]

    def get_searchable_columns(self):
        columns = self.get_table_metadata()["columns"]
        searchable_cols = [c["name"] for c in columns if c['searchable']]
        return searchable_cols
    
    def get_col_q_obj(self, col, query_value):
        custom_search_fn = getattr(self, f'{col}_Q_obj', None)
        
        if custom_search_fn:
            return custom_search_fn(query_value)
        else:
            if col in self.native_fields:
                return Q(**{f"{col}__icontains": query_value})
            else:
                return Q() # for custom fields search will only work if custom search is implemented

        


    def search_across_all_fields(self, objects, query_value):
        """
        Returns a queryset of the model where any of its fields contains the query_value.
        """
        searchable_cols = self.get_searchable_columns()
        q_objects = Q()
        for col in searchable_cols:
                q_objects |= self.get_col_q_obj(col, query_value)
        print(q_objects)
        return objects.filter(q_objects)
    
    def get_sorted_objects(self, objects, sort_col, sort_type):
        columns = self.get_columns()
        print("sort_type", sort_type)
        custom_sort_fn = getattr(self, f'{sort_col}_get_sorted_objects', None)
        if custom_sort_fn:
            return custom_sort_fn(objects, sort_type)
        else:
            if sort_type == 'asc':
                sort = f"-{sort_col}"
            else:
                sort = f"{sort_col}"
            return objects.order_by(sort)
    
    def get_data(self, request) -> list[dict]:
        objects = self.model.objects.all()
        if request.GET.get('search[value]'):
            objects = self.search_across_all_fields(objects, request.GET.get('search[value]'))
        #TODO: objects should be sliced to pagination size at this point    
        # SORT Objects
        sort_by_col = request.GET.get('order[0][column]', None)
        print("sort_by_col==>", sort_by_col )
        if sort_by_col:
            sort_type = request.GET.get('order[0][dir]') 
            sort_col = self.get_columns()[int(sort_by_col)-1]  
            print(self.get_columns())    
            print("sort_col", sort_col)     
            objects = self.get_sorted_objects(objects, sort_col, sort_type)
        else:
            objects = objects.order_by('-modified_at')
        return objects

        



