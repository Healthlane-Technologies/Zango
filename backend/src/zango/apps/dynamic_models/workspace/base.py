from __future__ import annotations

import inspect
import json
import os
import re

from collections import defaultdict

from django.conf import settings
from django.db import connection

from zango.apps.appauth.models import UserRoleModel
from zango.apps.dynamic_models.models import DynamicModelBase
from zango.apps.permissions.models import PolicyModel
from zango.core.custom_pluginbase import get_plugin_source

from .lifecycle import Lifecycle
from .wtree import WorkspaceTreeNode


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
        self.routes = self.get_all_view_urls()
        self.models = []  # sorted with bfs

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
        except Exception:
            pass
        if request:
            user = request.user
            if user.is_anonymous:
                role = UserRoleModel.objects.get(name="AnonymousUsers")
                return role.has_perm(request, "userAccess")
            else:
                from zango.core.utils import get_current_role

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
                    # Convert dotted module path to filesystem path (e.g., "parent.child" -> "parent/child")
                    # This allows packages to have nested module structures just like app modules
                    fs_path = mod["path"].replace(".", "/")
                    path = self.get_package_path(item["name"]) + fs_path
                    if path not in modules:
                        modules.append(path.replace(".", "/"))
            if item["type"] == "module":
                # Convert dotted module path to filesystem path (e.g., "parent.child" -> "parent/child")
                # This allows app modules to have nested structures
                fs_path = item["path"].replace(".", "/")
                path = self.path + fs_path
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

    def is_package_model(self, model_name: str) -> bool:
        return model_name.split(".")[2] == "packages"

    def load_models(self, migration=False, packages_only=False) -> None:
        """
        get topologically sorted list of models from packages and modules and
        import models.py files in that order
        """
        for m in self.get_models():
            if self.is_package_model(m) and migration:
                continue
            split = m.split(".")[2:]
            module = self.plugin_source.load_plugin(".".join(split))
            from zango.apps.auditlogs.registry import auditlog

            for name, obj in inspect.getmembers(module):
                if (
                    isinstance(obj, type)
                    and issubclass(obj, DynamicModelBase)
                    and obj != DynamicModelBase
                ):
                    dynamic_meta = getattr(obj, "DynamicModelMeta", None)
                    if dynamic_meta:
                        if getattr(dynamic_meta, "exclude_audit_log", False):
                            continue

                        excluded_fields = getattr(
                            dynamic_meta, "exclude_audit_log_fields", None
                        )
                        if excluded_fields:
                            auditlog.register(obj, exclude_fields=excluded_fields)
                        else:
                            auditlog.register(obj)
                    else:
                        auditlog.register(obj)
        return

    def sync_tasks(self, tenant_name) -> None:
        """
        get topologically sorted list of tasks from packages and modules and
        import tasks.py files in that order
        """
        import inspect

        from celery import Task

        from zango.apps.tasks.models import AppTask
        from zango.apps.tasks.utils import get_crontab_obj

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
        routes = _settings["app_routes"].copy()

        # Create a mapping of module names to their actual paths
        module_path_map = {
            module["name"]: module["path"] for module in _settings["modules"]
        }

        # Update routes to use actual module paths instead of just names
        for route in routes:
            if route["module"] in module_path_map:
                route["module"] = module_path_map[route["module"]]

        package_routes = _settings["package_routes"]
        for route in package_routes:
            pkg_settings = self.get_package_settings(route["package"])
            pkg_app_routes = pkg_settings["app_routes"]

            # Create a mapping of module names to their actual paths for this package
            pkg_module_path_map = {
                module["name"]: module["path"] for module in pkg_settings["modules"]
            }

            for pkg_route in pkg_app_routes:
                # Map module name to actual path if it exists in the mapping
                module_path = pkg_module_path_map.get(
                    pkg_route["module"], pkg_route["module"]
                )

                routes.append(
                    {
                        "re_path": route["re_path"] + pkg_route["re_path"].strip("^"),
                        "module": "packages." + route["package"] + "." + module_path,
                        "url": pkg_route["url"],
                    }
                )
        return routes

    def get_all_view_urls(self) -> list[dict]:
        """
        Returns URLs of all views in the workspace by examining urlpatterns
        from each module defined in get_root_urls()
        """
        all_urls = []
        root_urls = self.get_root_urls()

        for root_url in root_urls:
            try:
                module_path = root_url["module"] + "." + root_url["url"]
                module = self.plugin_source.load_plugin(module_path)
                urlpatterns = getattr(module, "urlpatterns", [])

                for pattern in urlpatterns:
                    # Construct full URL by combining root path and pattern
                    root_path = root_url["re_path"].strip("^$")
                    pattern_str = str(pattern.pattern).strip("^$")
                    full_url = "/" + root_path.strip("/") + "/" + pattern_str.strip("/")
                    full_url = re.sub(r"/+", "/", full_url)  # Remove duplicate slashes

                    url_info = {
                        "root_path": root_url["re_path"],
                        "module": root_url["module"],
                        "pattern": str(pattern.pattern),
                        "full_url": full_url,
                        "name": getattr(pattern, "name", None),
                        "callback": pattern.view_class[3:]
                        if getattr(pattern, "view_class", None)
                        else None,
                        "full_module_path": module_path,
                    }
                    all_urls.append(url_info)

            except Exception:
                # Skip modules that can't be loaded or don't have urlpatterns
                continue

        return all_urls

    def generate_dot_diagram(self, **options):
        """
        Generate a DOT diagram for the dynamic models in this workspace.

        Args:
            **options: Configuration options for the graph generation
                - disable_fields (bool): Don't show model fields
                - group_models (bool): Group models in subgraphs
                - verbose_names (bool): Use verbose field names
                - include_models (str/list): Models to include (supports wildcards)
                - exclude_models (str/list): Models to exclude (supports wildcards)
                - inheritance (bool): Show inheritance relationships
                - hide_edge_labels (bool): Hide relationship labels
                - rankdir (str): Graph layout direction
                - output_format (str): Output format ('dot', 'png', 'svg', 'json')
                - output_file (str): Output file path (for image formats)
                - layout (str): GraphViz layout algorithm ('dot', 'neato', 'fdp', etc.)

        Returns:
            str: DOT format string if output_format is 'dot' or None
            dict: JSON data if output_format is 'json'
            None: If output is written to file
        """
        from ..graph_utils import (
            DynamicModelGraphGenerator,
            generate_dot_from_data,
            render_output_pydot,
            render_output_pygraphviz,
        )

        # Set default options
        default_options = {
            "disable_fields": False,
            "group_models": False,
            "verbose_names": False,
            "inheritance": True,
            "hide_edge_labels": False,
            "output_format": "dot",
            "layout": "dot",
        }
        default_options.update(options)

        # Create graph generator
        graph_generator = DynamicModelGraphGenerator(
            tenant_name=self.wobj.name, **default_options
        )

        # Generate graph data
        graph_generator.generate_graph_data()

        output_format = default_options.get("output_format", "dot")
        output_file = default_options.get("output_file")

        if output_format == "json":
            graph_data = graph_generator.get_graph_data(as_json=True)
            if output_file:
                import json

                with open(output_file, "w") as f:
                    json.dump(graph_data, f, indent=2)
                return None
            return graph_data

        # Generate DOT data
        graph_data = graph_generator.get_graph_data(as_json=False)
        dotdata = generate_dot_from_data(graph_data)

        if output_format == "dot":
            if output_file:
                with open(output_file, "w") as f:
                    f.write(dotdata)
                return None
            return dotdata

        # For image formats, we need an output file
        if not output_file:
            raise ValueError("output_file is required for image formats")

        if output_format in ["png", "svg", "pdf"] or output_file.endswith(
            (".png", ".svg", ".pdf")
        ):
            # Try pygraphviz first, then pydot
            try:
                render_output_pygraphviz(
                    dotdata, output_file, layout=default_options.get("layout", "dot")
                )
            except ImportError:
                try:
                    render_output_pydot(dotdata, output_file)
                except ImportError:
                    raise ImportError(
                        "Neither pygraphviz nor pydot is available. "
                        "Install one of them to generate image output."
                    )
            return None

        # For any other format, return the DOT data
        return dotdata

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
        """
        Syncs policies defined in each module and package with the PolicyModel.

        This method iterates over all modules and packages within the workspace and checks for a 'policies.json' file.
        If found, it parses the file to retrieve policy definitions and saves or updates them.

        Raises:
            Exception: If there's an error parsing the policy file or creating/updating the PolicyModel instance.

        Notes:
            - The policy file should follow a specific structure:
                {
                    "policies": [
                        {
                            "name": "PolicyName",
                            "description": "Description of the policy",
                            "statement": {
                                "permissions": [
                                    {
                                        "name": "customers.views.CustomerCrudView",
                                        "type": "view"
                                    }
                                ]
                            }
                        },
                        ...
                    ]
                }
            - Policies with the same name and path are updated if they already exist.
            - Existing policies not found in the modules or packages are deleted.
        """
        existing_policies = list(
            PolicyModel.objects.filter(type="user").values_list("id", flat=True)
        )
        policy_roles = defaultdict(list)
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
                    # For nested modules, take all parts except the last one (which is "policies")
                    # This handles both simple modules (auth) and nested modules (test_mod.test_sub)
                    module_parts = model_module.split(".")[
                        2:-1
                    ]  # Remove workspace prefix and "policies" suffix
                    policy_path = ".".join(module_parts)
                with open(policy_file) as f:
                    try:
                        policy = json.load(f)
                    except json.decoder.JSONDecodeError as e:
                        raise Exception(f"Error parsing {policy_file}: {e}")
                    for policy_details in policy["policies"]:
                        if not isinstance(policy_details["statement"], dict):
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
                                    raise Exception("Policy name already exists")
                                existing_policies.remove(policy.id)
                            roles = policy_details.get("roles", None)
                            if roles is not None:
                                policy_roles[policy.id].extend(roles)
                        except Exception as e:
                            raise Exception(
                                f"Error creating policy {policy_details['name']} in {policy_path}: {e}"
                            )

        for policy_id in existing_policies:
            PolicyModel.objects.get(id=policy_id).delete()
        self.sync_policies_with_roles(policy_roles)

    def sync_policies_with_roles(self, policy_roles):
        """
        mapping roles from policies.json to UserRoleModel
        """
        for policy_id, roles in policy_roles.items():
            try:
                policy = PolicyModel.objects.get(id=policy_id)
                role_ids = [
                    UserRoleModel.objects.get(name=role).id
                    for role in roles
                    if UserRoleModel.objects.filter(name=role).exists()
                ]
                policy.role_policies.set(role_ids)
            except Exception as e:
                raise Exception(f"Error adding roles to policy {policy.name}: {e}")
            except UserRoleModel.DoesNotExist:
                raise Exception("Role does not exist")

    def sync_role_policies(self):
        for policy in PolicyModel.objects.all():
            if not policy.path:
                continue
            if policy.path and "packages" in policy.path:
                continue
            roles = policy.role_policies.all()
            # Convert dotted path (test_mod.test_sub) to filesystem path (test_mod/test_sub)
            fs_path = policy.path.replace(".", "/")
            with open(f"{self.path}/{fs_path}/policies.json", "r") as f:
                policies = json.load(f)
                for policy_details in policies["policies"]:
                    if policy_details["name"] == policy.name:
                        policy_details["roles"] = [role.name for role in roles]
            with open(f"{self.path}/{fs_path}/policies.json", "w") as f:
                json.dump(policies, f, indent=4)
