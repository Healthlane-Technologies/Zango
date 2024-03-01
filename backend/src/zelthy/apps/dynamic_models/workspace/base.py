from __future__ import annotations
import json
import os
import re

from django.conf import settings
from django.db import connection

from zelthy.apps.permissions.models import PolicyModel

# from zelthy.core.pluginbase1 import PluginBase, PluginSource

from .lifecycle import Lifecycle
from .wtree import WorkspaceTreeNode
from zelthy.apps.appauth.models import UserRoleModel

# class CustomPluginSource(PluginSource):
#     def load_plugin(self, name):
#         with self:
#             return __import__(self.base.package + '.' + name,
#                               globals(), {}, ['__name__'])

# class CustomPluginBase(PluginBase):

#     def make_plugin_source(self, *args, **kwargs):
#         """Creates a plugin source for this plugin base and returns it.
#         All parameters are forwarded to :class:`PluginSource`.
#         """
#         return CustomPluginSource(self, *args, **kwargs)

# from zelthy.core.custom_pluginbase import CustomPluginSource, CustomPluginBase
# # dummy python package to act as container for plugins
# plugin_base = CustomPluginBase(package='_workspaces')


# def get_plugin_source(name):
#     path = str(settings.BASE_DIR) + "/workspaces/" + name
#     return plugin_base.make_plugin_source(searchpath=[path])

from zelthy.core.custom_pluginbase import get_plugin_source

# import gc
# gc.set_debug(gc.DEBUG_LEAK)


class Workspace:
    """
    This is the main interface for interacting with the workspace codebase.
    Workspace is initialized under the request response cycle. It is
    reponsible for checking the integrity of the codebase and its dependencies.
    It also returns the view module and the name for the incoming request.

    Typical usage:

        For serving requests:
        ws = Workspace(request.tenant) Workspace(request=None, as_systemuser=False)
        ws.ready() #  loads the workspace models, sets sys.path, check etc.
        module, view, view_type = ws.get_view_module(request)
        request.add_middleware...

        response = getattr(import_module(module), view).as_view()(request, *args, **kwargs)
        response.add_middleware
        return response

        For code execution outside the request cycle (e.g. tasks, shell script):
        inside django shell (python manage.py tenant_command shell)
            ws = Workspace(connection.tenant)
            ws.ready() # loads the workspace models, sets sys.path, check etc.
    """

    _instances = {}

    def __new__(
        cls, wobj: object, request=None, as_systemuser=False, **kwargs
    ) -> object:
        # perform your permissions check here and tries to return the object from cache
        if not cls.check_perms(request, as_systemuser):
            raise ValueError("Permission denied.")
        key = wobj.name
        if key in cls._instances:
            return cls._instances[key]
        instance = super().__new__(cls)
        instance.plugin_source = cls.get_plugin_source()
        cls._instances[key] = instance
        return instance

    def __init__(self, wobj: object, request=None, as_systemuser=False) -> None:
        self.wobj = wobj
        self.path = str(settings.BASE_DIR) + f"/workspaces/{wobj.name}/"
        self.modules = self.get_ws_modules()
        self.packages = self.get_packages()
        self.models = []  # sorted with bfs
        # self.plugin_source = self.get_plugin_source()
        # self.wtee = self.get_wtree()

    @classmethod
    def get_plugin_source(cls):
        return get_plugin_source(connection.tenant.name)

    @classmethod
    def check_perms(cls, request=None, as_systemuser=False) -> None:
        """
        checks the perm for the workspace
        If user is Anonymous or SystemUser, then check access permission for the user role
        else check access permission for the user
        """
        try:
            if request.internal_routing:
                return True
        except:
            pass
        if request:
            user = request.user
            if user.is_anonymous:
                role = UserRoleModel.objects.get(name="AnonymousUsers")
                return role.has_perm(request, "userAccess")
            else:
                from zelthy.core.utils import get_current_role

                role = get_current_role()
                return role.has_perm(request, "userAccess")
        elif as_systemuser:
            # role = UserRoleModel.objects.get(name='SystemUser')
            return True

    def get_workspace_settings(self) -> dict:
        with open(self.path + "settings.json") as f:
            return json.loads(f.read())

    def get_version(self):
        return self.get_workspace_settings()["version"]

    def get_ws_modules(self) -> list[dict]:
        """
        returns workspaces' modules
        """
        _settings = self.get_workspace_settings()
        return _settings["modules"]

    def get_all_module_paths(self) -> list[str]:
        """
        returns path of all ws modules as well as package modules
        """
        modules = []
        ws_tree = self.get_wtree()
        bfs = ws_tree.bfs()
        bfs.reverse()
        for item in bfs:
            if item["type"] == "package":
                for mod in item["modules"]:
                    path = self.get_package_path(item["name"]) + mod["path"]
                    if path not in modules:
                        modules.append(path)
            if item["type"] == "module":
                path = self.path + item["path"]
                if path not in modules:
                    modules.append(path)
        return modules

    def get_models(self) -> list[str]:
        """
        returns sorted list of model modules (dependency first, then package then modules)
        """
        result = []
        modules = self.get_all_module_paths()
        for module in modules:
            if os.path.isfile(module + "/models.py"):
                model_module = (
                    module.replace(str(settings.BASE_DIR) + "/", "") + "/models"
                )
                model_module = model_module.lstrip("/").replace("/", ".")
                result.append(model_module)
        return result

    def get_tasks(self) -> list[str]:
        """
        returns sorted list of task modules (dependency first, then plugin then modules)
        """
        result = []
        modules = self.get_all_module_paths()
        for module in modules:
            if os.path.isfile(module + "/tasks.py"):
                model_module = (
                    module.replace(str(settings.BASE_DIR) + "/", "") + "/tasks"
                )
                model_module = model_module.lstrip("/").replace("/", ".")
                result.append(model_module)
        return result

    def get_packages(self) -> list[dict]:
        """
        returns list of packages
        """
        with open(self.path + "manifest.json") as f:
            return json.loads(f.read())["packages"]

    def get_package_path(self, package_name: str) -> str:
        return self.path + f"packages/{package_name}/"

    def get_package_settings(self, package_name: str) -> dict:
        _path = self.get_package_path(package_name) + "settings.json"
        with open(_path) as f:
            return json.loads(f.read())

    def get_package_modules(self, package_name: str) -> list[dict]:
        _settings = self.get_package_settings(package_name)
        return _settings["modules"]

    def get_package_dependencies(self, package_name: str) -> list[dict]:
        _path = self.get_package_path(package_name) + "settings.json"
        with open(_path) as f:
            _settings = json.loads(f.read())
            dependencies = _settings.get("dependencies", [])
        return dependencies

    def is_package_installed(self, package_name: str) -> bool:
        """
        the package and all its dependencies must be installed
        """
        if os.path.isfile(self.get_package_path(package_name) + "settings.json"):
            if len(self.get_package_dependencies(package_name)) == 0:
                return True
            else:
                for dep in self.get_package_dependencies(package_name):
                    if not os.path.isfile(
                        self.get_package_path(dep["name"]) + "settings.json"
                    ):
                        return False
                return True
        return False

    def all_packages_installed(self) -> bool:
        for package in self.get_packages():
            if not self.is_package_installed(package["name"]):
                return False
        return True

    def get_workspace_root_urls(self) -> list[dict]:
        pass

    def get_wtree(self):
        """
        returns workspace as tree of modules, packages and package dependencies
        """
        wtree = WorkspaceTreeNode({"name": "Root", "type": "root"})
        ws_settings = self.get_workspace_settings()
        for module in ws_settings["modules"]:
            wtree_appnode = WorkspaceTreeNode(
                {"name": module["name"], "type": "module", "path": module["path"]}
            )
            wtree.add_child(wtree_appnode)
        for package in self.get_packages():
            wtree_package = WorkspaceTreeNode(
                {
                    "name": package["name"],
                    "type": "package",
                    "modules": self.get_package_modules(package["name"]),
                }
            )
            for dependency in self.get_package_dependencies(package["name"]):
                wtree_package.add_child(
                    WorkspaceTreeNode(
                        {
                            "name": dependency["name"],
                            "type": "package",
                            "modules": self.get_package_modules(dependency["name"]),
                        }
                    )
                )
            wtree.add_child(wtree_package)
        return wtree

    def serve_request(self, request) -> tuple[str, str, str]:
        """
        returns the tuple of module, view name, view type (class or function)
        """
        pass

    def load_models(self, migration=False) -> None:
        """
        get topologically sorted list of models from packages and modules and
        import models.py files in that order
        """
        for m in self.get_models():
            if m.split(".")[2] == "packages" and migration:
                continue
            split = m.split(".")[2:]
            self.plugin_source.load_plugin(".".join(split))
        return

    def sync_tasks(self, tenant_name) -> None:
        """
        get topologically sorted list of tasks from packages and modules and
        import tasks.py files in that order
        """
        from zelthy.config.celery import app
        from celery import Task
        import inspect
        from zelthy.apps.tasks.models import AppTask
        from zelthy.apps.tasks.utils import get_crontab_obj

        task_ids_synced = []

        for m in self.get_tasks():
            mod_path = m.split(".")[2:]
            mod_path_str = ".".join(mod_path)
            _plugin = self.plugin_source.load_plugin(mod_path_str)

            for name, method in inspect.getmembers(_plugin):
                if isinstance(method, Task):
                    task_path = f"{mod_path_str}.{name}"
                    try:
                        task = AppTask.objects.get(name=task_path)
                        if task.is_deleted:
                            task.is_deleted = False
                            task.save()
                        task_ids_synced.append(task.id)
                    except AppTask.DoesNotExist:
                        schedule, success = get_crontab_obj()
                        task_obj, created = AppTask.objects.get_or_create(
                            name=task_path,
                            crontab=schedule,
                            args=[],
                            kwargs={},
                        )
                        if created:
                            task_obj.args = json.dumps([tenant_name, task_obj.name])
                            task_obj.save()
                        task_ids_synced.append(task_obj.id)
        AppTask.objects.all().exclude(id__in=task_ids_synced).update(
            is_deleted=True, is_enabled=False
        )

        return

    def ready(self) -> bool:
        """
        packages must be installed
        all models loaded
        migrations in sync
        """
        if not self.all_packages_installed():
            return False
        self.load_models()
        return

    def get_root_urls(self) -> list[dict]:
        _settings = self.get_workspace_settings()
        routes = _settings["app_routes"]
        package_routes = _settings["package_routes"]
        for route in package_routes:
            pkg_app_routes = self.get_package_settings(route["package"])["app_routes"]
            for pkg_route in pkg_app_routes:
                routes.append(
                    {
                        "re_path": route["re_path"] + pkg_route["re_path"].strip("^"),
                        "module": "packages."
                        + route["package"]
                        + "."
                        + pkg_route["module"],
                        "url": pkg_route["url"],
                    }
                )
        return routes

    def match_view(self, request) -> object:
        routes = self.get_root_urls()
        path = request.path.lstrip("/")
        for r in routes:
            r_regex = re.compile(r["re_path"])
            if r_regex.search(path):  # match module
                module = r["module"] + "." + r["url"]
                md = self.plugin_source.load_plugin(module)
                urlpatterns = getattr(md, "urlpatterns")
                mod_url_path = path[len(r["re_path"].strip("^")) :] or "/"
                for pattern in urlpatterns:
                    resolve = pattern.resolve(mod_url_path)  # find view
                    if resolve:
                        match = pattern.pattern.regex.search(mod_url_path)
                        return pattern.callback, resolve

        return None, None

    def is_dev_started(self):
        """
        Check if development has been started by evaluating the existence of modules or packages.
        """
        return self.modules or self.packages

    def launch(self, params: dict) -> None:
        """
        launch workspace, provision folders with boilerplate code, run migration
        """
        return Lifecycle.launch(params)

    def makemigrations(self):
        return None

    def migrate(self):
        return

    def sync_policies(self):
        existing_policies = list(
            PolicyModel.objects.filter(type="user").values_list("id", flat=True)
        )
        modules = self.get_all_module_paths()
        for module in modules:
            policy_file = f"{module}/policies.json"
            if os.path.isfile(policy_file):
                model_module = (
                    module.replace(str(settings.BASE_DIR) + "/", "") + "/policies"
                )
                model_module = model_module.lstrip("/").replace("/", ".")
                if "packages" in model_module:
                    policy_path = ".".join(model_module.split(".")[2:5])
                else:
                    policy_path = model_module.split(".")[2]
                with open(policy_file) as f:
                    try:
                        policy = json.load(f)
                    except json.decoder.JSONDecodeError as e:
                        raise Exception(f"Error parsing {policy_file}: {e}")
                    for policy_details in policy["policies"]:
                        if type(policy_details["statement"]) is not dict:
                            raise Exception(
                                f"Policy {policy_details['name']} has an invalid statement"
                            )
                        try:
                            policy, created = PolicyModel.objects.update_or_create(
                                name=policy_details["name"],
                                path=policy_path,
                                defaults={
                                    "description": policy_details.get(
                                        "description", ""
                                    ),
                                    "type": "user",
                                    "statement": policy_details["statement"],
                                },
                            )
                            if not created:
                                if policy.id not in existing_policies:
                                    raise Exception(f"Policy name already exists")
                                existing_policies.remove(policy.id)
                        except Exception as e:
                            raise Exception(
                                f"Error creating policy {policy_details['name']} in {policy_path}: {e}"
                            )

        for policy_id in existing_policies:
            PolicyModel.objects.get(id=policy_id).delete()
