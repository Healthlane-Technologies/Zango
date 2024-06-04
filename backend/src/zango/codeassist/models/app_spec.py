import os
import subprocess
from typing import List, Dict
from pydantic import BaseModel, Field
import json
import requests

from .policy import Policies, Policy, Permission, Statement
from .models import Model
from .crud import CrudView
from .packages.frame import Frame
from .packages.login import LoginConfig, GenericLoginConfig
from .packages.frame import Frame

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


class Role(BaseModel):
    name: str
    policies: List[List[str]]

    def apply(self, tenant):
        from zango.apps.permissions.models import PolicyModel
        from zango.apps.appauth.models import UserRoleModel

        try:
            role = UserRoleModel.objects.get(name=self.name)
        except UserRoleModel.DoesNotExist:
            role = UserRoleModel.objects.create(name=self.name)
            role.save()
        for policy in self.policies:
            try:
                policy = PolicyModel.objects.get(name=policy[0], path=policy[1])
            except PolicyModel.DoesNotExist:
                pass
            role.policies.add(policy)


class Module(BaseModule):
    models: List[Model] = Field(default_factory=list)
    migrate_models: bool = Field(default=False)
    views: List[CrudView] = Field(default_factory=list)

    def apply(self, tenant):
        if not os.path.exists(os.path.join("workspaces", tenant, self.name)):
            os.mkdir(os.path.join("workspaces", tenant, self.name))
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
        policies.apply(tenant, self.name)
        resp = requests.post(
            f"{URL}/generate-urls",
            json=json.dumps({"views": [v.name for v in self.views]}),
            headers={"Content-Type": "application/json"},
        )
        with open(os.path.join("workspaces", tenant, self.name, "urls.py"), "w") as f:
            f.write(resp.json()["content"])
        for view in self.views:
            view.apply(tenant, self.name)


class PackageConfigs(BaseModel):
    frame: List[Frame] | None = Field(default_factory=list)
    login: List[LoginConfig] | None = Field(default_factory=list)
    genericLoginConfig: GenericLoginConfig | None = GenericLoginConfig()

    def apply(self):
        for frame in self.frame:
            frame.apply()
        for login in self.login:
            login.apply()
        self.genericLoginConfig.apply()


class ApplicationSpec(BaseModel):
    modules: List[Module]
    tenant: str
    package_configs: PackageConfigs | None = PackageConfigs()
    roles: List[Role] = Field(default_factory=list)

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
        self.package_configs.apply()
        settings = Settings(
            version="0.1.0",
            modules=[
                BaseModule(name=module.name, path=module.path)
                for module in self.modules
            ],
            app_routes=[
                AppRoute(module=module.name, url="{{ url }}") for module in self.modules
            ],
        )
        settings.apply(self.tenant)
        for role in self.roles:
            role.apply(self.tenant)
