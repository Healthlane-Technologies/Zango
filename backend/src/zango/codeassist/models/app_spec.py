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

from zango.codeassist import URL
from zango.core.package_utils import install_package
from zango.codeassist.models.packages.frame import MenuItem


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
            allow_from_anywhere = PolicyModel.objects.get(name="AllowFromAnywhere")
            role.policies.add(allow_from_anywhere)
            role.save()
            try:
                frame_router = PolicyModel.objects.get(
                    name="FrameRouterViewAccess", path="packages.frame.router"
                )
                role.policies.add(frame_router)
                role.save()
            except PolicyModel.DoesNotExist:
                pass
        for policy in self.policies:
            try:
                policy_obj = PolicyModel.objects.get(name=policy[0], path=policy[1])
            except PolicyModel.DoesNotExist:
                pass
            role.policies.add(policy_obj)
            role.save()


class Module(BaseModule):
    models: List[Model] = Field(default_factory=list)
    migrate_models: bool = Field(default=True)
    views: List[CrudView] = Field(default_factory=list)

    def apply(self, tenant):
        if not os.path.exists(os.path.join("workspaces", tenant, self.name)):
            os.mkdir(os.path.join("workspaces", tenant, self.name))
        for model in self.models:
            model.apply(tenant, self.name)
        if self.migrate_models:
            subprocess.run(f"python manage.py ws_makemigration {tenant}", shell=True)
            # subprocess.run(f"python manage.py ws_migrate {tenant}", shell=True)
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
            view.apply(tenant, self.name, self.models)


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


class Package(BaseModel):
    name: str
    version: str

    def apply(self, tenant):
        resp = install_package(self.name, self.version, tenant)
        print(f"Installing package {self.name} {self.version}: {resp} ")
        if resp != "Package already installed":
            if getattr(self, f"post_install_{self.name}", None):
                getattr(self, f"post_install_{self.name}")(tenant)

    def post_install_login(self, tenant):
        from zango.apps.permissions.models import PolicyModel
        from zango.apps.appauth.models import UserRoleModel

        try:
            role = UserRoleModel.objects.get(name="AnonymousUsers")
            login_access = PolicyModel.objects.get(
                name="LoginViewAccess", path="packages.login.appauth"
            )
            role.policies.add(login_access)
            role.save()
        except Exception as e:
            print(e)
            return


class ApplicationSpec(BaseModel):
    modules: List[Module]
    app_name: str
    domain: str
    package_configs: PackageConfigs | None = PackageConfigs()
    roles: List[Role] = Field(default_factory=list)
    packages: List[Package] = Field(default_factory=list)

    def apply(self):
        self.packages = [
            Package(name="frame", version="0.5.1"),
            Package(name="login", version="0.5.1"),
            Package(name="workflow", version="0.3.0"),
            Package(name="crud", version="0.3.0"),
        ]
        for package in self.packages:
            package.apply(self.app_name)
        if not os.path.exists(
            os.path.join(
                "workspaces",
                self.app_name,
            )
        ):
            os.mkdir(
                os.path.join(
                    "workspaces",
                    self.app_name,
                )
            )
        settings = Settings(
            version="0.1.0",
            modules=[
                BaseModule(name=module.name, path=module.path)
                for module in self.modules
            ],
            app_routes=[
                AppRoute(module=module.name, re_path=f"^{module.name}/", url="urls")
                for module in self.modules
            ],
        )
        settings.apply(self.app_name)
        for module in self.modules:
            module.apply(self.app_name)
        for role in self.roles:
            role.apply(self.app_name)

        for frame in self.package_configs.frame:
            menu = []
            for module in self.modules:
                for view in module.views:
                    if frame.role in view.roles:
                        resp = json.loads(
                            requests.post(
                                f"{URL}/generate-frame-menu",
                                json={
                                    "url": f"{module.name}/",
                                    "view_name": view.name,
                                },
                            ).json()["content"]
                        )
                        menu.append(
                            MenuItem(
                                url=resp["url"],
                                name=resp["title"],
                            )
                        )
            frame.menu = menu
        self.package_configs.apply()
