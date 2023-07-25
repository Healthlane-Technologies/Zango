from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class DjangoModelConverter:
    def __init__(self, django_model):
        self.django_model = django_model
        self.sqlalchemy_model = None

    def convert_to_sqlalchemy(self):
        fields = {
            'id': Column(Integer, primary_key=True),
        }

        for field in self.django_model._meta.fields:
            if field.name == 'id':
                continue

            field_type = self._get_sqlalchemy_field_type(field)
            kwargs = self._get_sqlalchemy_field_kwargs(field)
            fields[field.name] = Column(field_type, **kwargs)

        self.sqlalchemy_model = type(self.django_model.__name__, (Base,), fields)

        # Handle many-to-many relationships
        for field in self.django_model._meta.many_to_many:
            if isinstance(field.remote_field.model, str):
                continue

            association_table_name = f'{self.django_model.__name__.lower()}_{field.name}'
            association_table = self._create_association_table(field, association_table_name)
            setattr(self.sqlalchemy_model, field.name, relationship(
                field.remote_field.model,
                secondary=association_table,
                back_populates=self._get_back_populates_name(field),
            ))

        return self.sqlalchemy_model

    def _get_sqlalchemy_field_type(self, field):
        # Map common Django field types to SQLAlchemy field types
        django_to_sqlalchemy = {
            'CharField': String,
            'IntegerField': Integer,
            'BooleanField': Boolean,
            # Add more mappings for other field types as needed
        }
        field_type = django_to_sqlalchemy.get(field.__class__.__name__)
        if field_type is None:
            raise ValueError(f"Unsupported field type: {field.__class__.__name__}")
        return field_type

    def _get_sqlalchemy_field_kwargs(self, field):
        kwargs = {}

        if field.primary_key:
            kwargs['primary_key'] = True

        if not field.null:
            kwargs['nullable'] = False

        # Add more specific kwargs based on the field attributes as needed

        return kwargs

    def _create_association_table(self, field, table_name):
        return Table(
            table_name,
            Base.metadata,
            Column('id', Integer, primary_key=True),
            Column(f'{field.name}_id', Integer, ForeignKey(f'{field.remote_field.model._meta.model.__name__.lower()}.id')),
            Column(f'{self.django_model.__name__.lower()}_id', Integer, ForeignKey(f'{self.django_model._meta.model.__name__.lower()}.id')),
        )

    def _get_back_populates_name(self, field):
        # Generate the name of the back_populates attribute for the SQLAlchemy relationship
        return f'{self.django_model.__name__.lower()}_{field.name}'
