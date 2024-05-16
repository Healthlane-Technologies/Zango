# Auditlogs

Adding audit logs to a system is a crucial step towards enhancing security, accountability, and transparency.
We have used the version 3.0.0 of the library [django-auditlog](https://github.com/jazzband/django-auditlog) to add support for auditlog in the zelthy framework while implementing some changes to suit our framework

## Changes Made To `django-auditlog` Library

### AuditLog Model Change

- Zango framework contains an object store which can be used to retrieve an object of any type using the object UUID, so an additional field was added to the auditlog table, this field is a foreign key which points to the object store entry for that particular model

- Zango framework defines two types of users - App User and Platform User, to accurately store which user performed a particular action, two foreign keys Platform Actor and Tenant Actor were added to the LogEntry model to log which user performed the action

### Register Changes

In the zelthy3 framework by default all the core models and the dynamic models will be registered for auditlogs automatically, to control which models and fields of dynamic models need to be logged a custom meta class for DynamicModels `DynamicModelMeta` can be used

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

### File Changes

**Note:** Import statements are modified from `from auditlog` to `from zelthy.apps.auditlogs` the rest of the import statement remains the same

1. `__init__.py`

`__version__` removed

2. `admin.py`

Import statements modified

3. `apps.py`

Import statements modified
django app name changed - `auditlog` to `zango.apps.auditlogs`

4. `conf.py`

Import statements modified
`set_actor` method is modified to assign platform_actor or tenant actor based on the actor performing the action

5. `diff.py`

Import statements modified
`ZforeignKey` and `ZOneToOneField` handled in `get_field_value` method

6. `middleware.py`

Import statements modified
`_get_actor` method tries to get the platform user if the type of the `User` returned is `AnonymousUser` as this case occurs when platform user is authenticated using token

7. `mixins.py`

Import statements modified

8. `receivers.py`

Import statements modified

9. `registry.py`

Import statements modified
