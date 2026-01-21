import json
import os
import traceback

from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.utils.decorators import method_decorator

from zango.apps.dynamic_models.graph_utils import DynamicModelGraphGenerator
from zango.apps.dynamic_models.workspace.base import Workspace
from zango.core.api import (
    TenantMixin,
    ZangoGenericPlatformAPIView,
    get_api_response,
)
from zango.core.common_utils import set_app_schema_path
from zango.core.package_utils import get_installed_packages
from zango.core.permissions import IsPlatformUserAllowedApp

from .serializers import AppCodebaseSerializer


@method_decorator(set_app_schema_path, name="dispatch")
class AppCodebaseViewAPIV1(ZangoGenericPlatformAPIView, TenantMixin):
    permission_classes = (IsPlatformUserAllowedApp,)

    def analyze_module(self, module_path):
        """Analyze a module directory for additional details"""
        module_info = {
            "models_count": 0,
            "views_count": 0,
            "templates_count": 0,
            "has_urls": False,
            "has_policies": False,
            "models": [],
        }

        try:
            # Check for models.py
            models_file = module_path / "models.py"
            if models_file.exists():
                model_details = self.extract_model_details(models_file)
                module_info["models_count"] = len(model_details)
                module_info["models"] = model_details

            # Check for views.py or views directory
            views_file = module_path / "views.py"
            views_dir = module_path / "views"
            if views_file.exists():
                module_info["views_count"] = 1
            elif views_dir.exists() and views_dir.is_dir():
                module_info["views_count"] = len(list(views_dir.glob("*.py")))

            # Check for templates directory
            templates_dir = module_path / "templates"
            if templates_dir.exists() and templates_dir.is_dir():
                module_info["templates_count"] = len(
                    list(templates_dir.rglob("*.html"))
                )

            # Check for urls.py and extract routes
            urls_file = module_path / "urls.py"
            module_info["has_urls"] = urls_file.exists()

            # Check for policies.json
            policies_file = module_path / "policies.json"
            module_info["has_policies"] = policies_file.exists()

        except Exception as e:
            print(f"Error analyzing module {module_path}: {str(e)}")

        return module_info

    def extract_model_details(self, models_file):
        """Extract model details using DynamicModelGraphGenerator"""
        models = []

        try:
            # Check if models file actually exists
            if not models_file.exists():
                return models

            # Get tenant name from connection
            tenant_name = connection.tenant.name if connection.tenant else None
            if not tenant_name:
                print(
                    f"Warning: No tenant context available for extracting models from {models_file}"
                )
                return models

            # Get the module path from the models_file path
            workspace_path = f"{settings.BASE_DIR}/workspaces/{tenant_name}/"
            relative_path = str(models_file.parent.relative_to(workspace_path))
            module_path = relative_path.replace("/", ".")

            # Create graph generator and get only models from this specific module
            graph_generator = DynamicModelGraphGenerator(tenant_name=tenant_name)

            # Get only dynamic models for this specific module (optimized)
            try:
                dynamic_models = graph_generator.get_module_dynamic_models(module_path)
            except Exception as e:
                print(
                    f"Warning: Could not load dynamic models for module {module_path}: {e}"
                )
                return models

            # Convert dynamic models to the expected format
            # Note: dynamic_models already contains only models from the specified module
            for model in dynamic_models:
                try:
                    model_context = graph_generator.get_model_context(model)

                    # Convert to the format expected by the API
                    model_info = {
                        "name": model_context["name"],
                        "fields": [],
                        "relationships": [],
                        "meta": {},
                    }

                    # Add verbose name to meta if available
                    if (
                        hasattr(model._meta, "verbose_name")
                        and model._meta.verbose_name
                    ):
                        model_info["meta"]["verbose_name"] = str(
                            model._meta.verbose_name
                        )

                    # Add db_table to meta if available
                    if hasattr(model._meta, "db_table") and model._meta.db_table:
                        model_info["meta"]["db_table"] = model._meta.db_table

                    # Process fields
                    for field_data in model_context["fields"]:
                        if field_data.get("relation", False):
                            # This is a relationship field
                            relationship_info = {
                                "name": field_data["name"],
                                "type": field_data["type"],
                                "attributes": {},
                            }

                            # Add field attributes
                            if field_data.get("blank"):
                                relationship_info["attributes"]["blank"] = field_data[
                                    "blank"
                                ]

                            # Try to get related model from field
                            field = field_data.get("field")
                            if (
                                field
                                and hasattr(field, "remote_field")
                                and field.remote_field
                            ):
                                if hasattr(field.remote_field, "model"):
                                    related_model = field.remote_field.model
                                    if hasattr(related_model, "__name__"):
                                        relationship_info["related_model"] = (
                                            related_model.__name__
                                        )
                                    elif isinstance(related_model, str):
                                        relationship_info["related_model"] = (
                                            related_model
                                        )

                                # Add on_delete info if available
                                if hasattr(field.remote_field, "on_delete"):
                                    on_delete = field.remote_field.on_delete
                                    if hasattr(on_delete, "__name__"):
                                        relationship_info["attributes"]["on_delete"] = (
                                            on_delete.__name__
                                        )

                                # Add related_name if available
                                if (
                                    hasattr(field.remote_field, "related_name")
                                    and field.remote_field.related_name
                                ):
                                    relationship_info["attributes"]["related_name"] = (
                                        field.remote_field.related_name
                                    )

                            model_info["relationships"].append(relationship_info)
                        else:
                            # This is a regular field
                            field_info = {
                                "name": field_data["name"],
                                "type": field_data["type"],
                                "attributes": {},
                            }

                            # Add field attributes
                            if field_data.get("blank"):
                                field_info["attributes"]["blank"] = field_data["blank"]

                            # Get additional attributes from the actual field
                            field = field_data.get("field")
                            if field:
                                if hasattr(field, "null"):
                                    field_info["attributes"]["null"] = field.null
                                if hasattr(field, "max_length") and field.max_length:
                                    field_info["attributes"]["max_length"] = (
                                        field.max_length
                                    )
                                if (
                                    hasattr(field, "default")
                                    and field.default is not None
                                ):
                                    # Convert default to string representation for JSON serialization
                                    try:
                                        field_info["attributes"]["default"] = str(
                                            field.default
                                        )
                                    except Exception:
                                        pass

                            model_info["fields"].append(field_info)

                    # Process relationships from model context
                    for relation in model_context["relations"]:
                        # Skip if this relation is already captured as a field
                        relation_name = relation.get("name", "")
                        if not any(
                            rel["name"] == relation_name
                            for rel in model_info["relationships"]
                        ):
                            relationship_info = {
                                "name": relation_name,
                                "type": relation.get("type", "Unknown"),
                                "related_model": relation.get("target", ""),
                                "attributes": {},
                            }
                            model_info["relationships"].append(relationship_info)

                    models.append(model_info)

                except Exception as e:
                    print(f"Warning: Could not process model {model.__name__}: {e}")
                    continue

        except Exception as e:
            print(f"Error extracting model details from {models_file}: {str(e)}")
            return models

        return models

    def get(self, request, *args, **kwargs):
        try:
            # Get the app tenant
            tenant = self.get_tenant(**kwargs)
            connection.set_tenant(tenant)
            with connection.cursor() as c:
                ws = Workspace(connection.tenant, request=None, as_systemuser=True)
                view_urls = ws.get_all_view_urls()

                # Generate DOT diagram with error handling
                try:
                    dot_diagram = ws.generate_dot_diagram()
                except Exception as e:
                    print(f"Warning: Could not generate DOT diagram: {e}")
                    dot_diagram = None
            app_name = tenant.schema_name

            # Construct workspace path
            workspace_path = Path(settings.BASE_DIR) / "workspaces" / app_name
            settings_file_path = workspace_path / "settings.json"

            if not workspace_path.exists():
                return get_api_response(
                    False,
                    {"message": f"Workspace directory not found for app: {app_name}"},
                    404,
                )

            response_data = {
                "app_name": app_name,
                "workspace_path": str(workspace_path),
                "settings_file_exists": settings_file_path.exists(),
                "dot_diagram": dot_diagram,
            }

            if settings_file_path.exists():
                # Read and parse settings.json
                with open(settings_file_path, "r") as f:
                    settings_data = json.load(f)

                # Get file modification time
                stat = os.stat(settings_file_path)
                response_data["last_modified"] = datetime.fromtimestamp(stat.st_mtime)

                # Process settings data
                response_data["version"] = settings_data.get("version", "unknown")

                # Process modules with additional analysis
                modules = settings_data.get("modules", [])
                for module in modules:
                    module_path = workspace_path / module["path"].replace(".", "/")
                    if module_path.exists():
                        module_analysis = self.analyze_module(module_path)
                        module.update(module_analysis)

                response_data["modules"] = modules
                response_data["package_routes"] = settings_data.get(
                    "package_routes", []
                )
                response_data["app_routes"] = settings_data.get("app_routes", [])

                # Build route tree
                response_data["route_tree"] = view_urls

                # Calculate statistics
                response_data["total_modules"] = len(modules)
                installed_packages = get_installed_packages(app_name)
                response_data["total_packages"] = len(installed_packages)
                response_data["total_routes"] = len(
                    settings_data.get("package_routes", [])
                ) + len(settings_data.get("app_routes", []))
            else:
                # If settings.json doesn't exist, try to scan the workspace
                response_data["version"] = "unknown"
                response_data["modules"] = []
                response_data["package_routes"] = []
                response_data["app_routes"] = []
                response_data["total_modules"] = 0
                response_data["total_packages"] = 0
                response_data["total_routes"] = 0

            # Serialize the response
            serializer = AppCodebaseSerializer(data=response_data)
            if serializer.is_valid():
                return get_api_response(
                    True,
                    {
                        "app_codebase": serializer.data,
                        "message": "App codebase details fetched successfully",
                    },
                    200,
                )
            else:
                return get_api_response(
                    False,
                    {"message": "Error serializing data", "errors": serializer.errors},
                    400,
                )

        except Exception as e:
            traceback.print_exc()
            return get_api_response(False, {"message": str(e)}, 500)
