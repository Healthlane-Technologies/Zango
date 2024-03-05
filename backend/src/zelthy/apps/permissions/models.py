import uuid
from django.db.models import Q
from django.db import models
from django.db.models import JSONField
from django.db.models.query import QuerySet
from zelthy.core.model_mixins import FullAuditMixin


class PermissionsModel(FullAuditMixin):
    name = models.CharField("Name of the permission", max_length=100, unique=True)
    type = models.CharField(
        "Type of the permission",
        max_length=50,
        choices=(
            ("view", "View"),
            ("datamodel", "DataModel"),
            ("user_access", "User Access"),
            ("custom", "Custom"),
        ),
    )

    def __str__(self):
        return self.name

    @classmethod
    def sync_perms(cls):
        """
        inspects the codebase and syncs the permissions
        """
        from django.db import connection

        app_dir = get_app_base_dir(connection.tenant)
        # iterate through all views and add view perms
        app_settings = get_app_settings(connection.tenant)
        # routes = get_app_settings(connection.tenant)['routes']
        routes = get_root_routes(connection.tenant)
        for route in routes:
            url_file = get_mod_url_filepath(connection.tenant, route["module"])
            with url_file.open() as f:
                _url_file = f.read()
            # zcode = ZPreprocessor(
            #               _url_file,
            #               tenant=connection.tenant,
            #               parent_path=url_file.parent,
            #               app_dir=app_dir,
            #               app_settings=app_settings
            #               )
            # c = ZimportStack(zcode, tenant=connection.tenant)
            # c.process_import_and_execute()
            # urlpatterns = c._globals['urlpatterns']
            for pattern in urlpatterns:
                if pattern.callback.__name__ == "view":
                    view_name = pattern.callback.view_class.__name__
                else:
                    view_name = pattern.callback.__name__
                # perms.append(route["module"]+"/"+view_name)
                cls.objects.get_or_create(
                    name=route["module"] + "/" + view_name, type="view"
                )

        # iterate through all datamodels and add datamodel perms

        return


class PolicyModel(FullAuditMixin):
    POLICY_TYPES = [
        ("system", "SYSTEM"),
        ("user", "USER"),
    ]

    name = models.CharField("Name of the policy", max_length=50)
    path = models.CharField("Policy path", max_length=300, blank=True, null=True)
    description = models.CharField(
        "Description of the policy", max_length=300, blank=True
    )
    statement = JSONField(null=True)
    expiry = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    type = models.CharField(choices=POLICY_TYPES, max_length=10, default="user")

    def __str__(self):
        return self.name

    @classmethod
    def get_valid_policies(cls):
        return cls.objects.filter(
            Q(expiry__gte=timezone.now()) | Q(expiry__isnull=True)
        )

    @classmethod
    def get_userAccess_policies(cls):
        valid_policies = cls.get_valid_policies()
        return valid_policies.filter(
            statement__permissions__contains=[{"type": "userAccess"}]
        )

    class Meta:
        unique_together = ("name", "path")


class PolicyGroupModel(FullAuditMixin):
    name = models.CharField("Name of the policy group", max_length=50, unique=True)
    description = models.CharField(
        "Description of the policy group", max_length=300, blank=True
    )
    policies = models.ManyToManyField(PolicyModel, related_name="policy_groups")

    def __str__(self):
        return self.name
