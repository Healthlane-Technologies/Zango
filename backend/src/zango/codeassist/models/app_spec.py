import os
import subprocess
from typing import List, Union
from pydantic import BaseModel
import json
import requests

from .policy import Policies, Policy, Statement, Permission
from .models import Model
from .crud import CrudView
from .packages.frame import Frame
from .packages.login import LoginConfig, GenericLoginConfig
from .workflow import WorkFlow
from .forms import Form
from .crud import CrudTable
from .detail import Detail
from .packages.frame import Frame
from .packages.login import LoginConfig, GenericLoginConfig

from zango.codeassist import URL, TENANT_URL


class BaseModule(BaseModel):
    name: str
    path: str


class AppRoute(BaseModel):
    module: str
    re_path: str
    url: str


class Settings(BaseModel):
    version: str
    modules: List[BaseModule]
    app_routes: List[AppRoute]

    def apply(self, tenant):
        package_routes = json.load(
            open(os.path.join("workspaces", tenant, "settings.json"), "r")
        ).get("package_routes")
        with open(os.path.join("workspaces", tenant, "settings.json"), "w") as f:
            f.write(f"{self.model_dump_json()}")
        settings = json.load(
            open(os.path.join("workspaces", tenant, "settings.json"), "r")
        )
        settings["package_routes"] = package_routes
        with open(os.path.join("workspaces", tenant, "settings.json"), "w") as f:
            f.write(f"{json.dumps(settings)}")


class Url(BaseModel):
    url: str
    view: str


class Module(BaseModule):
    models: List[Model] = []
    migrate_models: bool = False
    workflows: List[WorkFlow] = []
    tables: List[CrudTable]
    forms: List[Form] = []
    details: List[Detail] = []
    views: List[CrudView] = []
    settings: Settings
    urls: List[Url] | None = None

    def apply(self, tenant):
        if not os.path.exists(os.path.join("workspaces", tenant, self.name)):
            os.mkdir(os.path.join("workspaces", tenant, self.name))
        self.settings.apply(tenant)
        for model in self.models:
            model.apply(tenant, self.name)
        if self.migrate_models:
            subprocess.run(f"python manage.py ws_makemigration {tenant}", shell=True)
            subprocess.run(f"python manage.py ws_migrate {tenant}", shell=True)
        policies = Policies(
            policies=[
                Policy(
                    name=f"{view.name}AccessPolicy",
                    description=f"{view.name} access policy",
                    statement=Statement(
                        permissions=[
                            Permission(
                                name=f"{self.name}.views.{view.name}", type="view"
                            )
                        ],
                    ),
                )
                for view in self.views
            ]
        )
        with open(
            os.path.join("workspaces", tenant, self.name, "policies.json"), "w"
        ) as f:
            f.write(f"{policies.model_dump_json()}")
        resp = requests.post(
            f"{URL}/generate-urls",
            json=json.dumps([{"url": url.url, "view": url.view} for url in self.urls]),
        )
        with open(os.path.join("workspaces", tenant, self.name, "urls.py"), "w") as f:
            f.write(resp.json()["content"])
        for view in self.views:
            view.apply(tenant, self.name)
        for table in self.tables:
            table.apply(tenant, self.name)
        for form in self.forms:
            form.apply(tenant, self.name)
        for detail in self.details:
            detail.apply(tenant, self.name)
        for workflow in self.workflows:
            workflow.apply(tenant, self.name)


class Role(BaseModel):
    name: str

    def apply(self, tenant):
        from zango.apps.appauth.models import UserRoleModel

        try:
            role = UserRoleModel.objects.get(name=self.name)
        except UserRoleModel.DoesNotExist:
            role = UserRoleModel.objects.create(name=self.name)
            role.save()


class ApplicationSpec(BaseModel):
    modules: List[Module]
    roles: List[Role] = []
    tenant: str
    package_configs: List[LoginConfig | GenericLoginConfig | Frame] = []

    def apply(self):
        if not os.path.exists(
            os.path.join(
                "workspaces",
                self.tenant,
            )
        ):
            os.mkdir(
                os.path.join(
                    "workspaces",
                    self.tenant,
                )
            )
        for module in self.modules:
            module.apply(self.tenant)
        for role in self.roles:
            role.apply(self.tenant)
        for package_config in self.package_configs:
            package_config.apply()
