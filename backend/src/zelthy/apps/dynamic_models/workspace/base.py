from __future__ import annotations
import json
import os
import re

from django.conf import settings
from django.db import connection
from django.http import Http404

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
        self.plugins = self.get_plugins()
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
        if request:
            user = request.user
            return True  # TODO: Remove this later
            if user.is_anonymous:
                role = UserRoleModel.objects.get(name="AnonymousUsers")
                return role.has_perm(request, "userAccess")
            else:
                return user.has_perm(request, "userAccess")
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
        returns path of all ws modules as well as plugin modules
        """
        modules = []
        ws_tree = self.get_wtree()
        bfs = ws_tree.bfs()
        bfs.reverse()
        for item in bfs:
            if item["type"] == "plugin":
                for mod in item["modules"]:
                    path = self.get_plugin_path(item["name"]) + mod["path"]
                    if path not in modules:
                        modules.append(path)
            if item["type"] == "module":
                path = self.path + item["path"]
                if path not in modules:
                    modules.append(path)
        return modules

    def get_models(self) -> list[str]:
        """
        returns sorted list of model modules (dependency first, then plugin then modules)
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

    def get_plugins(self) -> list[dict]:
        """
        returns list of plugins
        """
        with open(self.path + "plugins.json") as f:
            return json.loads(f.read())["plugins"]

    def get_plugin_path(self, plugin_name: str) -> str:
        return self.path + f"plugins/{plugin_name}/"

    def get_plugin_settings(self, plugin_name: str) -> dict:
        _path = self.get_plugin_path(plugin_name) + "settings.json"
        with open(_path) as f:
            return json.loads(f.read())

    def get_plugin_modules(self, plugin_name: str) -> list[dict]:
        _settings = self.get_plugin_settings(plugin_name)
        return _settings["modules"]

    def get_plugin_dependencies(self, plugin_name: str) -> list[dict]:
        _path = self.get_plugin_path(plugin_name) + "settings.json"
        with open(_path) as f:
            _settings = json.loads(f.read())
            dependencies = _settings.get("dependencies", [])
        return dependencies

    def is_plugin_installed(self, plugin_name: str) -> bool:
        """
        the plugin and all its dependencies must be installed
        """
        if os.path.isfile(self.get_plugin_path(plugin_name) + "settings.json"):
            if len(self.get_plugin_dependencies(plugin_name)) == 0:
                return True
            else:
                for dep in self.get_plugin_dependencies(plugin_name):
                    if not os.path.isfile(
                        self.get_plugin_path(dep["name"]) + "settings.json"
                    ):
                        return False
                return True
        return False

    def all_plugins_installed(self) -> bool:
        for plugin in self.get_plugins():
            if not self.is_plugin_installed(plugin["name"]):
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
        for plugin in self.get_plugins():
            wtree_plugin = WorkspaceTreeNode(
                {
                    "name": plugin["name"],
                    "type": "plugin",
                    "modules": self.get_plugin_modules(plugin["name"]),
                }
            )
            for dependency in self.get_plugin_dependencies(plugin["name"]):
                wtree_plugin.add_child(
                    WorkspaceTreeNode(
                        {
                            "name": dependency["name"],
                            "type": "plugin",
                            "modules": self.get_plugin_modules(dependency["name"]),
                        }
                    )
                )
            wtree.add_child(wtree_plugin)
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
            if m.split(".")[2] == "plugins" and migration:
                continue
            split = m.split(".")[2:]
            self.plugin_source.load_plugin(".".join(split))
        return

    def ready(self) -> bool:
        """
        plugins must be installed
        all models loaded
        migrations in sync
        """
        if not self.all_plugins_installed():
            return False
        self.load_models()
        return

    def get_root_urls(self) -> list[dict]:
        _settings = self.get_workspace_settings()
        routes = _settings["app_routes"]
        package_routes = _settings["plugin_routes"]
        for route in package_routes:
            pkg_app_routes = self.get_plugin_settings(route["plugin"])["app_routes"]
            for pkg_route in pkg_app_routes:
                routes.append(
                    {
                        "re_path": route["re_path"] + pkg_route["re_path"].strip("^"),
                        "module": "plugins."
                        + route["plugin"]
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

        raise Http404()

    def launch(self, params: dict) -> None:
        """
        launch workspace, provision folders with boilerplate code, run migration
        """
        return Lifecycle.launch(params)

    def makemigrations(self):
        return None

    def migrate(self):
        return
