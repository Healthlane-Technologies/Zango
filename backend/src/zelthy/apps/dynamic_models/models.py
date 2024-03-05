import uuid
from functools import reduce
from operator import and_

from django.db import models, connection
from django.db.models import Q
from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType

from zelthy.apps.appauth.models import AppUserModel
from zelthy.core.utils import get_current_request, get_current_role
from zelthy.apps.shared.platformauth.models import PlatformUserModel
from zelthy.apps.dynamic_models.permissions import is_platform_user

from zelthy.apps.object_store.models import ObjectStore


class RegisterOnceModeMeta(type(models.Model)):
    pass

    def __new__(mcs, name, bases, attrs):
        if apps.ready:
            try:
                model = apps.get_model("dynamic_models", name)
                return model  # Model already registered. Won't register twice
            except LookupError:
                model = super().__new__(mcs, name, bases, attrs)
                return model
        model = super().__new__(mcs, name, bases, attrs)
        return model


class DefaultAppsProxy:
    """
    A proxy class to the default apps registry.
    This class is needed to make our dynamic models available in the
    options when the relation tree is built.
    """

    def __init__(self):
        self._extra_models = []

    def add_models(self, *dynamic_models):
        """
        Adds a model to the default apps registry.
        """
        self._extra_models.extend(dynamic_models)

    def get_models(self, *args, **kwargs):
        return apps.get_models(*args, **kwargs) + self._extra_models

    def __getattr__(self, attr):
        return getattr(apps, attr)


class ORMPemissions:
    permissions = {}

    @property
    def request(self):
        return get_current_request()

    def update_model_perm(self, model_name):
        self.model_name = model_name
        self.user_role = get_current_role()
        actions = []
        records = []
        for perm in self.get_permissions(model_name):
            actions += perm["actions"]
            records.append(perm["records"])
        self.permissions[self.request.tenant.name] = {
            self.user_role.id: {
                model_name: {"actions": list(set(actions)), "records": records}
            }
        }

    def get_permissions(self, model_name):
        permissions = []
        policies = self.user_role.get_policies("model", model=model_name)
        for policy in policies:
            perms = policy.statement["permissions"]
            for perm in perms:
                if perm["type"] == "model" and perm["name"] == self.model_name:
                    permissions.append(perm)
        return permissions

    # def get_allowed_attrs(self, attr_perm):
    #     """
    #         either all fields are permissioned or only specified fields are permissioned
    #         not supporting all_except
    #     """
    #     if "only" in attr_perm:
    #         return attr_perm["only"]
    #     elif "all" in attr_perm and attr_perm["all"]:
    #         return "__all__"
    #     else:
    #         return [] # block all attributes by default


def build_q_from_spec(spec):
    """
    simple filtering
        "records": {"field": "f", "operation": "icontains", "value": "val"}
    complex filtering
        "records": {
            "logical_operator": "or", "conditions": [{"field": "username", "operation": "equals",
        "value": "john_doe"},{"field": "email", "operation": "icontains", "value": "@example.com"}
        }
    nested:
        "records": { "logical_operator": "or", "conditions": [ { "field": "username", "operation": "equals", "value": "john_doe" }, { "logical_operator": "and", "conditions": [ { "field": "first_name", "operation": "equals", "value": "John" }, { "field": "last_name", "operation": "equals", "value": "Doe" } ] } ] }
    conditions:
    """
    if "field" in spec:
        if spec["operation"] and spec["operation"] != "equals":
            operation = f"{spec['field']}__{spec['operation']}"
        else:
            operation = f"{spec['field']}"
        return Q(**{operation: spec["value"]})

    if "logical_operator" in spec:
        q_objects = [build_q_from_spec(condition) for condition in spec["conditions"]]
        if spec["logical_operator"] == "and":
            return Q(*q_objects)
        elif spec["logical_operator"] == "or":
            return reduce(lambda x, y: x | y, q_objects)

    raise ValueError("Invalid specification")


def replace_special_context(data):
    """
    Recursively replace values containing {{}} with a special object.
    """
    if isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, (dict, list)):
                data[index] = replace_special_context(item)

    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                data[key] = replace_special_context(value)
            elif isinstance(value, str) and "{{" in value and "}}" in value:
                if value == "{{user}}":
                    data[
                        key
                    ] = AppUserModel.objects.all().first()  # get_current_request().user
                elif value == "{{user_role}}":
                    data[key] = get_current_role()
                elif value == "{{user_role_id}}":
                    data[key] = get_current_role().id
    return data


class RestrictedQuerySet(models.QuerySet, ORMPemissions):
    permissions = None

    def __init__(self, model=None, query=None, using=None, hints=None):
        super().__init__(model=model, query=query, using=using, hints=hints)
        ormPermObj = ORMPemissions()
        request = get_current_request()
        self.platform_user = False
        if is_platform_user(request):
            self.platform_user = True
        else:
            ormPermObj.update_model_perm(model.__name__)
            self.permissions = ormPermObj.permissions
            self.tenant_name = connection.tenant.name
            self.user_role_id = get_current_role().id

    def has_perm(self, perm_type):
        return (
            perm_type
            in self.permissions[self.tenant_name][self.user_role_id][
                self.model.__name__
            ]["actions"]
        )

    def prefilter(self):
        specs = self.permissions[self.tenant_name][self.user_role_id][
            self.model.__name__
        ]["records"]
        filter_qs = [build_q_from_spec(replace_special_context(spec)) for spec in specs]
        combined_q = reduce(and_, filter_qs)
        return super().filter(combined_q)

    def get(self, *args, **kwargs):
        if self.platform_user:
            return super(RestrictedQuerySet, self).get(*args, **kwargs)
        if self.has_perm("view"):
            prefiltered_qs = self.prefilter()
            obj = super(RestrictedQuerySet, prefiltered_qs).get(*args, **kwargs)
            return obj
        raise PermissionDenied(
            "View permission not available for {self.model.__name__}"
        )

    def all(self):
        if self.platform_user:
            return super(RestrictedQuerySet, self).all()
        if self.has_perm("view"):
            prefiltered_qs = self.prefilter()
            qs = super(RestrictedQuerySet, prefiltered_qs).all()
            return qs
        raise PermissionDenied(
            "View permission not available for {self.model.__name__}"
        )

    def exclude(self, *args, **kwargs):
        if self.platform_user:
            return super(RestrictedQuerySet, self).exclude(*args, **kwargs)
        if self.has_perm("view"):
            prefiltered_qs = self.prefilter()
            qs = super(RestrictedQuerySet, prefiltered_qs).exclude(*args, **kwargs)
            return qs
        raise PermissionDenied(
            "View permission not available for {self.model.__name__}"
        )

    def filter(self, *args, **kwargs):
        if self.platform_user:
            return super(RestrictedQuerySet, self).filter(*args, **kwargs)
        if self.has_perm("view"):
            prefiltered_qs = self.prefilter()
            qs = super(RestrictedQuerySet, prefiltered_qs).filter(*args, **kwargs)
            return qs
        raise PermissionDenied(
            "View permission not available for {self.model.__name__}"
        )

    def annotate(self, *args, **kwargs):
        if self.platform_user:
            return super(RestrictedQuerySet, self).annotate(*args, **kwargs)
        if self.has_perm("view"):
            prefiltered_qs = self.prefilter()
            qs = super(RestrictedQuerySet, prefiltered_qs).annotate(*args, **kwargs)
            return qs
        raise PermissionDenied(
            "View permission not available for {self.model.__name__}"
        )

    def aggregate(self, *args, **kwargs):
        if self.platform_user:
            return super(RestrictedQuerySet, self).aggregate(*args, **kwargs)
        if self.has_perm("view"):
            prefiltered_qs = self.prefilter()
            qs = super(RestrictedQuerySet, prefiltered_qs).aggregate(*args, **kwargs)
            return qs
        raise PermissionDenied(
            "View permission not available for {self.model.__name__}"
        )

    def select_related(self, *args, **kwargs):
        if self.platform_user:
            return super(RestrictedQuerySet, self).select_related(*args, **kwargs)
        if self.has_perm("view"):
            prefiltered_qs = self.prefilter()
            qs = super(RestrictedQuerySet, prefiltered_qs).select_related(
                *args, **kwargs
            )
            return qs
        raise PermissionDenied(
            "View permission not available for {self.model.__name__}"
        )

    def create(self, *args, **kwargs):
        if self.platform_user:
            return super().create(*args, **kwargs)
        if self.has_perm("create"):
            return super().create(*args, **kwargs)
        raise PermissionDenied(
            f"Create permission not available for {self.model.__name__}"
        )

    def bulk_create(self, *args, **kwargs):
        if self.platform_user:
            return super().bulk_create(*args, **kwargs)
        if self.has_perm("create"):
            return super().bulk_create(*args, **kwargs)
        raise PermissionDenied(
            f"Create permission not available for {self.model.__name__}"
        )

    def update(self, *args, **kwargs):
        if self.platform_user:
            return super().update(*args, **kwargs)
        if self.has_perm("edit"):
            return super().update(*args, **kwargs)
        raise PermissionDenied(
            f"Edit permission not available for {self.model.__name__}"
        )

    def bulk_update(self, *args, **kwargs):
        if self.platform_user:
            return super().bulk_update(*args, **kwargs)
        if self.has_perm("edit"):
            return super().bulk_update(*args, **kwargs)
        raise PermissionDenied(
            f"Edit permission not available for {self.model.__name__}"
        )

    def delete(self):
        if self.platform_user:
            return super().delete()
        if self.has_perm("delete"):
            return super().delete()
        raise PermissionDenied(
            f"Delete permission not available for {self.model.__name__}"
        )

    def values(self, *fields, **expressions):
        return super().values(*fields, **expressions)


class RestrictedManager(models.Manager):
    def get_queryset(self):
        qs = RestrictedQuerySet(self.model, using=self._db)
        return qs

    def all(self):
        qs = RestrictedQuerySet(self.model, using=self._db)
        return qs.all()


class DynamicModelBase(models.Model, metaclass=RegisterOnceModeMeta):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        AppUserModel, null=True, editable=False, on_delete=models.PROTECT
    )
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(
        AppUserModel, null=True, editable=False, on_delete=models.PROTECT
    )
    object_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # objects = RestrictedManager()

    class Meta:
        app_label = "dynamic_models"
        apps = DefaultAppsProxy()
        abstract = True

    def has_perm(self, perm_type):
        if not isinstance(self.__class__.objects, RestrictedQuerySet):
            return True
        model_name = self.__class__.__name__
        perm_obj = ORMPemissions()
        perm_obj.update_model_perm(model_name)
        permissions = perm_obj.permissions
        current_role_id = get_current_role().id
        tenant_name = connection.tenant.name
        if (
            perm_type
            in permissions[tenant_name][current_role_id][type(self).__name__]["actions"]
        ):
            return True
        return False

    # TODO: Attribute level permission
    # def __getattribute__(self, key):
    #     """
    #         returns AttributeError if view perm is not available for the field
    #         being accessed
    #         if `create` or `edit` perm is available then this check is not required
    #     """
    #     whitelisted_keys = ['__class__', '_meta', '__dict__', '_state', 'id', 'pk'] + \
    #         list(vars(models.Model).keys())

    #     if key not in whitelisted_keys:
    #         perm_obj = ORMPemissions()
    #         perm_obj.update_model_perm(type(self).__name__)
    #         permissions = perm_obj.permissions
    #         current_role_id = get_current_role().id
    #         tenant_name = connection.tenant.name
    #         allowed_attrs =permissions[tenant_name]\
    #             [current_role_id][type(self).__name__]["allowed_attrs"]
    #         actions = permissions[tenant_name][current_role_id][type(self).__name__]["actions"]
    #         if not any(action in actions for action in ["create", "edit"]):
    #             if key not in allowed_attrs:
    #                 raise AttributeError(f"'{type(self).__name__}' permission not available for '{key}'")
    #     return super().__getattribute__(key)

    def save(self, *args, **kwargs):
        request = get_current_request()
        is_create_operation = not self.pk
        if is_platform_user(request):
            return super().save(*args, **kwargs)
        if is_create_operation and self.has_perm("create"):
            resp = super().save(*args, **kwargs)

            # Create an object in ObjectStore when object is getting created
            content_type = ContentType.objects.get_for_model(self)
            ObjectStore.objects.create(
                object_uuid=self.object_uuid,
                content_type=content_type,
                object_id=self.pk,
                content_object=self,
            )
            return resp
        if self.pk and self.has_perm("edit"):
            return super().save(*args, **kwargs)
        raise PermissionDenied(
            f"Create/Edit Permission not available for {self.__class__.__name__}"
        )

    def delete(self, *args, **kwargs):
        request = get_current_request()
        if is_platform_user(request):
            return super().delete(*args, **kwargs)
        if self.has_perm("delete"):
            return super().delete(*args, **kwargs)
        raise PermissionDenied(
            f"Delete Permission not available for {self.__class__.__name__}"
        )
