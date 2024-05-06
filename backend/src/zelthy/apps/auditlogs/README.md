# Auditlogs

Adding audit logs to a system is a crucial step towards enhancing security, accountability, and transparency.
We have used the version 3.0.0 of the library [django-auditlog](https://github.com/jazzband/django-auditlog) to add support for auditlog in the ZCore framework while implementing some changes to suit our framework

## Changes Made To `django-auditlog` Library

### AuditLog Model Change

ZCore framework contains an object store which can be used to retrieve an object of any type using the object UUID, so an additional field was added to the auditlog table, this field is a foreign key which points to the object store entry for that particular model

### Register Changes

In the ZCore framework by default all the core models and the dynamic models will be registered for auditlogs automatically, to control which models and fields of dynamic models need to be logged a custom meta class for DynamicModels `DynamicModelMeta` can be used

eg: To exclude a model
```python
class Model(DynamicModelBase):
    # Fields ...

    class DynamicModelMeta:
        exclude_audit_log = True
```

eg: To exclude fields
```python
class Model(DynamicModelBase):
    # Fields ...

    class DynamicModelMeta:
        exclude_audit_log_fields = ['field1', 'field2']
```

