import os
import subprocess
from typing import List, Union
from pydantic import BaseModel
import json
import requests

from .policy import Policies
from .models import Model
from .crud import CrudView
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
    policies: Policies | None = None
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
        if self.policies:
            with open(
                os.path.join("workspaces", tenant, self.name, "policies.json"), "w"
            ) as f:
                f.write(f"{self.policies.model_dump_json()}")

        resp = requests.post(
            f"{URL}/generate-urls",
            json=json.dumps([{"url": url.url, "view": url.view} for url in self.urls]),
        )
        with open(os.path.join("workspaces", tenant, self.name, "urls.py"), "w") as f:
            f.write(resp.json()["content"])
        for view in self.views:
            view.apply(tenant, self.name)


class Role(BaseModel):
    name: str
    frame: Frame | None = None
    login: LoginConfig | None = None
    generic_login: GenericLoginConfig | None = None

    def apply(self, tenant):
        from zango.apps.appauth.models import UserRoleModel

        try:
            role = UserRoleModel.objects.get(name=self.name)
        except UserRoleModel.DoesNotExist:
            role = UserRoleModel.objects.create(name=self.name)
            role.save()

        if self.frame:
            requests.post(
                f"{TENANT_URL}/frame/configure/orm/",
                data={
                    "user_role_id": role.pk,
                    "config": json.loads(self.frame.model_dump_json()),
                },
                headers={"Content-Type": "application/json"},
            )
        if self.login:
            requests.post(
                f"{TENANT_URL}/login/configure/orm/loginconfig/",
                data={
                    "user_role_id": role.pk,
                    "config": json.loads(self.login.model_dump_json()),
                },
                headers={"Content-Type": "application/json"},
            )
        if self.generic_login:
            requests.post(
                f"{TENANT_URL}/login/configure/orm/genericloginconfig/",
                data={
                    "config": json.loads(self.generic_login.model_dump_json()),
                },
                headers={"Content-Type": "application/json"},
            )


class ApplicationSpec(BaseModel):
    modules: List[Module]
    roles: List[Role] = []
    tenant: str

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
