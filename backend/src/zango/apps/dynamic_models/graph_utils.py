"""
Graph utilities for generating DOT diagrams from Zango dynamic models.
This module provides functionality to generate GraphViz DOT format output
for dynamic models in a workspace.
"""

import fnmatch
import inspect
import json
import os
import tempfile

from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection

from zango.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField
from zango.apps.dynamic_models.models import DynamicModelBase
from zango.core.custom_pluginbase import get_plugin_source


try:
    import pygraphviz  # type: ignore

    HAS_PYGRAPHVIZ = True
except ImportError:
    HAS_PYGRAPHVIZ = False

try:
    try:
        import pydotplus as pydot  # type: ignore
    except ImportError:
        import pydot  # type: ignore
    HAS_PYDOT = True
except ImportError:
    HAS_PYDOT = False


class DynamicModelGraphGenerator:
    """
    Graph generator for Zango's dynamic models system.
    Replaces Django's apps.get_models() with dynamic model discovery.
    """

    def __init__(self, tenant_name=None, **kwargs):
        self.graphs = []
        self.tenant_name = tenant_name or (
            connection.tenant.name if connection.tenant else None
        )

        if not self.tenant_name:
            raise ValueError(
                "No tenant specified. Provide tenant_name or ensure tenant is set in connection."
            )

        self.cli_options = kwargs.get("cli_options", None)
        self.disable_fields = kwargs.get("disable_fields", False)
        self.disable_abstract_fields = kwargs.get("disable_abstract_fields", False)
        self.include_models = self._parse_file_or_list(kwargs.get("include_models", ""))
        self.use_subgraph = kwargs.get("group_models", False)
        self.verbose_names = kwargs.get("verbose_names", False)
        self.inheritance = kwargs.get("inheritance", True)
        self.relations_as_fields = kwargs.get("relations_as_fields", True)
        self.relation_fields_only = kwargs.get("relation_fields_only", False)
        self.sort_fields = kwargs.get("sort_fields", True)
        self.language = kwargs.get("language", None)
        self.exclude_columns = self._parse_file_or_list(
            kwargs.get("exclude_columns", "")
        )
        self.exclude_models = self._parse_file_or_list(kwargs.get("exclude_models", ""))
        self.hide_edge_labels = kwargs.get("hide_edge_labels", False)
        self.arrow_shape = kwargs.get("arrow_shape", "dot")
        self.color_code_deletions = kwargs.get("color_code_deletions", False)
        self.rankdir = kwargs.get("rankdir")
        self.display_field_choices = kwargs.get("display_field_choices", False)
        self.ordering = kwargs.get("ordering")

    def _parse_file_or_list(self, arg):
        """Parse file or comma-separated list argument"""
        if not arg:
            return []
        if isinstance(arg, (list, tuple, set)):
            return arg
        if "," not in arg and os.path.isfile(arg):
            return [e.strip() for e in open(arg).readlines()]
        return [e.strip() for e in arg.split(",")]

    def get_workspace_dynamic_models(self):
        """
        Get all dynamic models for the current tenant/workspace.
        This replaces Django's apps.get_models() for dynamic models.
        """
        workspace_path = f"{settings.BASE_DIR}/workspaces/{self.tenant_name}/"
        plugin_source = get_plugin_source(self.tenant_name)

        # Check if workspace exists
        if not os.path.exists(workspace_path):
            raise ValueError(
                f"Workspace '{self.tenant_name}' not found at {workspace_path}"
            )

        # Check if settings.json exists
        settings_file = os.path.join(workspace_path, "settings.json")
        if not os.path.exists(settings_file):
            raise ValueError(
                f"settings.json not found in workspace '{self.tenant_name}'"
            )

        with open(settings_file) as f:
            ws_settings = json.load(f)

        dynamic_models = []
        processed_models = set()

        # Get models from workspace modules
        for module_config in ws_settings.get("modules", []):
            module_path = module_config["path"]
            models_file = os.path.join(
                workspace_path, module_path.replace(".", "/"), "models.py"
            )

            if os.path.exists(models_file):
                try:
                    module = plugin_source.load_plugin(f"{module_path}.models")

                    for _, obj in inspect.getmembers(module):
                        if (
                            isinstance(obj, type)
                            and issubclass(obj, DynamicModelBase)
                            and obj != DynamicModelBase
                            and obj.__name__ not in processed_models
                        ):
                            dynamic_models.append(obj)
                            processed_models.add(obj.__name__)
                except Exception as e:
                    print(f"Warning: Could not load module {module_path}.models: {e}")

        # Package models are excluded from output as per requirements
        # They are not added to dynamic_models list

        return dynamic_models

    def get_module_dynamic_models(self, module_path):
        """
        Get dynamic models for a specific module only.
        More efficient when you need models from a single module.

        Args:
            module_path (str): Relative module path (e.g., "base_forms", "form_views")

        Returns:
            list: List of DynamicModelBase subclasses from the module
        """
        workspace_path = f"{settings.BASE_DIR}/workspaces/{self.tenant_name}/"
        plugin_source = get_plugin_source(self.tenant_name)

        # Check if workspace exists
        if not os.path.exists(workspace_path):
            raise ValueError(
                f"Workspace '{self.tenant_name}' not found at {workspace_path}"
            )

        dynamic_models = []
        models_file = os.path.join(
            workspace_path, module_path.replace(".", "/"), "models.py"
        )

        # Return empty list if models.py doesn't exist
        if not os.path.exists(models_file):
            return dynamic_models

        try:
            module = plugin_source.load_plugin(f"{module_path}.models")

            for _, obj in inspect.getmembers(module):
                if (
                    isinstance(obj, type)
                    and issubclass(obj, DynamicModelBase)
                    and obj != DynamicModelBase
                ):
                    dynamic_models.append(obj)
        except Exception as e:
            print(f"Warning: Could not load module {module_path}.models: {e}")

        return dynamic_models

    def generate_graph_data(self):
        """Generate graph data for dynamic models"""
        # Get all dynamic models
        dynamic_models = self.get_workspace_dynamic_models()

        if not dynamic_models:
            raise ValueError(
                f"No dynamic models found in workspace '{self.tenant_name}'"
            )

        # Create a single app context for all dynamic models
        app_graph = {
            "name": f'"dynamic_models_{self.tenant_name}"',
            "app_name": f"dynamic_models_{self.tenant_name}",
            "cluster_app_name": f"cluster_dynamic_models_{self.tenant_name}",
            "models": [],
        }

        # Process each model
        for model in dynamic_models:
            if not self.use_model(model.__name__):
                continue

            model_context = self.get_model_context(model)
            app_graph["models"].append(model_context)

        if app_graph["models"]:
            self.graphs.append(app_graph)

        # Generate relationships between models
        nodes = []
        for graph in self.graphs:
            nodes.extend([e["name"] for e in graph["models"]])

        for graph in self.graphs:
            for model in graph["models"]:
                for relation in model["relations"]:
                    if relation is not None:
                        if relation["target"] in nodes:
                            relation["needs_node"] = False
                        else:
                            # For external models (like AppUserModel, DynamicModelBase),
                            # allow the relationship but mark as external
                            relation["needs_node"] = False
                            relation["external_target"] = True

    def get_model_context(self, model):
        """Get context data for a single model"""
        from django.contrib.contenttypes.fields import GenericRelation
        from django.db.models import deletion
        from django.db.models.fields.related import (
            ForeignKey,
            ManyToManyField,
            OneToOneField,
            RelatedField,
        )
        from django.utils.encoding import force_str

        # Get model abstracts
        abstracts = [
            abstract_model.__name__
            for abstract_model in model.__bases__
            if hasattr(abstract_model, "_meta") and abstract_model._meta.abstract
        ]

        context = {
            "model": model,
            "app_name": f"dynamic_models_{self.tenant_name}",
            "name": model.__name__,
            "abstracts": abstracts,
            "fields": [],
            "relations": [],
        }

        if self.verbose_names and model._meta.verbose_name:
            context["label"] = force_str(model._meta.verbose_name)
        else:
            context["label"] = context["name"]

        # Get abstract fields from base classes
        abstract_fields = self.get_bases_abstract_fields(model)

        # Get model attributes
        if self.relations_as_fields:
            attributes = [field for field in model._meta.local_fields]
        else:
            attributes = [
                field
                for field in model._meta.local_fields
                if not isinstance(field, RelatedField)
            ]

        # Process primary key first
        pk = model._meta.pk
        if pk and not model._meta.abstract and pk in attributes:
            context["fields"].append(self.get_field_attributes(pk, abstract_fields))

        # Process other fields
        for field in attributes:
            if self.skip_field(field) or (pk and field == pk):
                continue
            context["fields"].append(self.get_field_attributes(field, abstract_fields))

        if self.sort_fields:
            context["fields"] = sorted(
                context["fields"],
                key=lambda field: (
                    not field["primary_key"],
                    not field["relation"],
                    field["label"],
                ),
            )

        # Process relations
        for field in model._meta.local_fields:
            if (
                field.attname.endswith("_ptr_id")
                or field in abstract_fields
                or self.skip_field(field)
            ):
                continue

            relation = None
            color = None

            if self.color_code_deletions and isinstance(
                field, (OneToOneField, ForeignKey, ZOneToOneField, ZForeignKey)
            ):
                field_on_delete = getattr(field.remote_field, "on_delete", None)
                on_delete_colors = {
                    deletion.CASCADE: "red",
                    deletion.PROTECT: "blue",
                    deletion.SET_NULL: "orange",
                    deletion.SET_DEFAULT: "green",
                    deletion.SET: "yellow",
                    deletion.DO_NOTHING: "grey",
                    deletion.RESTRICT: "purple",
                }
                color = on_delete_colors.get(field_on_delete)

            if isinstance(field, (OneToOneField, ZOneToOneField)):
                relation = self.add_relation(
                    field, "[arrowhead=none, arrowtail=none, dir=both]", color
                )
            elif isinstance(field, (ForeignKey, ZForeignKey)):
                relation = self.add_relation(
                    field,
                    f"[arrowhead=none, arrowtail={self.arrow_shape}, dir=both]",
                    color,
                )

            if relation is not None and self.use_model(relation["target"]):
                # Filter out common audit fields and DynamicModelBase inheritance by default
                if not self._should_skip_relation(relation):
                    context["relations"].append(relation)

        # Process many-to-many fields
        for field in model._meta.local_many_to_many:
            if self.skip_field(field):
                continue

            relation = None
            if isinstance(field, ManyToManyField):
                try:
                    remote_field = getattr(field, "remote_field", None)
                    if (
                        remote_field
                        and hasattr(remote_field, "through")
                        and hasattr(remote_field.through, "_meta")
                        and getattr(remote_field.through._meta, "auto_created", False)
                    ):
                        relation = self.add_relation(
                            field,
                            f"[arrowhead={self.arrow_shape} arrowtail={self.arrow_shape}, dir=both]",
                        )
                except AttributeError:
                    pass  # Skip if through table access fails
            elif isinstance(field, GenericRelation):
                relation = self.add_relation(
                    field,
                    '[style="dotted", arrowhead=normal, arrowtail=normal, dir=both]',
                )

            if relation is not None and self.use_model(relation["target"]):
                # Filter out common audit fields and DynamicModelBase inheritance by default
                if not self._should_skip_relation(relation):
                    context["relations"].append(relation)

        # Process inheritance
        if self.inheritance:
            for parent in model.__bases__:
                if hasattr(parent, "_meta"):  # parent is a model
                    label = "multi-table"
                    if parent._meta.abstract:
                        label = "abstract"
                    if model._meta.proxy:
                        label = "proxy"
                    label += r"\ninheritance"
                    if self.hide_edge_labels:
                        label = ""

                    inheritance_rel = {
                        "target_app": f"dynamic_models_{self.tenant_name}",
                        "target": parent.__name__,
                        "type": "inheritance",
                        "name": "inheritance",
                        "label": label,
                        "arrows": "[arrowhead=empty, arrowtail=none, dir=both]",
                        "needs_node": True,
                    }

                    if inheritance_rel not in context["relations"] and self.use_model(
                        inheritance_rel["target"]
                    ):
                        # Filter out common audit fields and DynamicModelBase inheritance by default
                        if not self._should_skip_relation(inheritance_rel):
                            context["relations"].append(inheritance_rel)

        return context

    def get_field_attributes(self, field, abstract_fields):
        """Get attributes for a single field"""
        from django.db.models.fields.related import (
            ForeignKey,
            OneToOneField,
            RelatedField,
        )
        from django.utils.encoding import force_str

        if self.verbose_names and field.verbose_name:
            label = force_str(field.verbose_name)
            if label.islower():
                label = label.capitalize()
        else:
            label = field.name

        t = type(field).__name__
        if isinstance(field, (OneToOneField, ForeignKey, ZOneToOneField, ZForeignKey)):
            try:
                remote_field = getattr(field, "remote_field", None)
                if remote_field and hasattr(remote_field, "field_name"):
                    field_name = getattr(remote_field, "field_name", None)
                    if field_name:
                        t += f" ({field_name})"
            except AttributeError:
                pass  # Skip if remote_field access fails
        if self.display_field_choices and hasattr(field, "choices") and field.choices:
            try:
                # Handle both callable and non-callable choices
                field_choices = (
                    field.choices() if callable(field.choices) else field.choices
                )
                if field_choices:
                    choices = {c for c, _ in field_choices}
                    t = str(choices)
            except (TypeError, ValueError, AttributeError):
                pass  # Skip if choices is not iterable or accessible

        return {
            "field": field,
            "name": field.name,
            "label": label,
            "type": t,
            "blank": field.blank,
            "abstract": any(
                (
                    hasattr(field, "creation_counter")
                    and hasattr(abstract_field, "creation_counter")
                    and getattr(field, "creation_counter", None)
                    == getattr(abstract_field, "creation_counter", None)
                )
                for abstract_field in abstract_fields
                if abstract_field
                and hasattr(field, "creation_counter")
                and hasattr(abstract_field, "creation_counter")
            ),
            "relation": isinstance(field, RelatedField),
            "primary_key": field.primary_key,
        }

    def get_bases_abstract_fields(self, model):
        """Get abstract fields from base classes"""
        abstract_fields = []
        for base in model.__bases__:
            if hasattr(base, "_meta") and base._meta.abstract:
                abstract_fields.extend(base._meta.fields)
                abstract_fields.extend(self.get_bases_abstract_fields(base))
        return abstract_fields

    def _should_skip_relation(self, relation):
        """
        Determine if a relation should be skipped based on default filtering rules.
        Skip common audit fields and DynamicModelBase inheritance by default.
        """
        target = relation.get("target", "")
        name = relation.get("name", "")
        relation_type = relation.get("type", "")

        # Skip DynamicModelBase inheritance (common to all dynamic models)
        if relation_type == "inheritance" and target == "DynamicModelBase":
            return True

        # Skip common audit fields (created_by, modified_by to AppUserModel)
        if target == "AppUserModel" and name in ("created_by", "modified_by"):
            return True

        return False

    def add_relation(self, field, extras="", color=None):
        """Add relation information for a field"""
        from django.apps import apps
        from django.utils.encoding import force_str

        if self.verbose_names and field.verbose_name:
            label = force_str(field.verbose_name)
            if label.islower():
                label = label.capitalize()
        else:
            label = field.name

        # Show related field name
        if hasattr(field, "related_query_name"):
            related_query_name = field.related_query_name()
            if self.verbose_names and related_query_name.islower():
                related_query_name = related_query_name.replace("_", " ").capitalize()
            label = f"{label} ({force_str(related_query_name)})"

        if self.hide_edge_labels:
            label = ""

        # Handle self-relationships and lazy-relationships
        if isinstance(field.remote_field.model, str):
            if field.remote_field.model == "self":
                target_model = field.model
            else:
                if "." in field.remote_field.model:
                    app_label, model_name = field.remote_field.model.split(".", 1)
                else:
                    app_label = field.model._meta.app_label
                    model_name = field.remote_field.model

                # For ZForeignKey and ZOneToOneField, try to resolve from dynamic models first
                if isinstance(field, (ZForeignKey, ZOneToOneField)):
                    try:
                        # Get all dynamic models for this tenant
                        dynamic_models = self.get_workspace_dynamic_models()
                        # Find the model by name
                        target_model = None
                        for model in dynamic_models:
                            if model.__name__ == model_name:
                                target_model = model
                                break

                        if target_model is None:
                            # Fallback to Django's apps registry
                            target_model = apps.get_model(app_label, model_name)
                    except Exception:
                        # Fallback to Django's apps registry
                        target_model = apps.get_model(app_label, model_name)
                else:
                    target_model = apps.get_model(app_label, model_name)
        else:
            target_model = field.remote_field.model

        if color:
            extras = f"[{extras[1:-1]}, color={color}]"

        return {
            "target_app": f"dynamic_models_{self.tenant_name}",
            "target": target_model.__name__,
            "type": type(field).__name__,
            "name": field.name,
            "label": label,
            "arrows": extras,
            "needs_node": True,
        }

    def use_model(self, model_name):
        """Decide whether to use a model based on include/exclude lists"""
        import re

        # Check against include list
        if self.include_models:
            for model_pattern in self.include_models:
                model_pattern = f"^{model_pattern.replace('*', '.*')}$"
                if re.search(model_pattern, model_name):
                    return True

        # Check against exclude list
        if self.exclude_models:
            for model_pattern in self.exclude_models:
                model_pattern = f"^{model_pattern.replace('*', '.*')}$"
                if re.search(model_pattern, model_name):
                    return False

        # Return True if include_models is falsey, otherwise return False
        return not self.include_models

    def skip_field(self, field):
        """Determine if a field should be skipped"""
        from django.db.models.fields.related import (
            ForeignKey,
            ManyToManyField,
            OneToOneField,
            RelatedField,
        )
        from django.db.models.fields.reverse_related import ManyToOneRel, OneToOneRel

        if self.exclude_columns:
            if self.verbose_names and field.verbose_name:
                if field.verbose_name in self.exclude_columns:
                    return True
            if field.name in self.exclude_columns:
                return True

        if self.relation_fields_only:
            if not isinstance(
                field,
                (
                    ForeignKey,
                    ManyToManyField,
                    OneToOneField,
                    RelatedField,
                    OneToOneRel,
                    ManyToOneRel,
                    ZForeignKey,
                    ZOneToOneField,
                ),
            ):
                return True

        return False

    def get_graph_data(self, as_json=False):
        """Get graph data for rendering"""
        import datetime

        now = datetime.datetime.now()
        graph_data = {
            "created_at": now.strftime("%Y-%m-%d %H:%M"),
            "cli_options": self.cli_options,
            "disable_fields": self.disable_fields,
            "disable_abstract_fields": self.disable_abstract_fields,
            "display_field_choices": self.display_field_choices,
            "use_subgraph": self.use_subgraph,
            "rankdir": self.rankdir,
            "ordering": self.ordering,
        }

        if as_json:
            # Remove model and field classes for JSON serialization
            graphs = []
            for context in self.graphs:
                graph_copy = context.copy()
                graph_copy["models"] = []
                for model_data in context["models"]:
                    model_copy = model_data.copy()
                    model_copy.pop("model", None)
                    fields_copy = []
                    for field_data in model_data["fields"]:
                        field_copy = field_data.copy()
                        field_copy.pop("field", None)
                        fields_copy.append(field_copy)
                    model_copy["fields"] = fields_copy
                    graph_copy["models"].append(model_copy)
                graphs.append(graph_copy)
            graph_data["graphs"] = graphs
        else:
            graph_data["graphs"] = self.graphs

        return graph_data


def generate_dot_from_data(graph_data):
    """Generate DOT format data from graph data without external templates"""
    dot_lines = [
        "digraph model_graph {",
        "  // Zango Dynamic Models Graph",
        '  fontname = "Helvetica"',
        "  fontsize = 8",
        "  splines = true",
        "  nodesep = 0.4",
        "  ranksep = 0.3",
        "",
    ]

    # Add rankdir if specified
    if graph_data.get("rankdir"):
        dot_lines.append(f"  rankdir = {graph_data['rankdir']}")

    # Add ordering if specified
    if graph_data.get("ordering"):
        dot_lines.append(f"  ordering = {graph_data['ordering']}")

    dot_lines.append("")

    # Process each graph (app)
    for graph in graph_data.get("graphs", []):
        if graph_data.get("use_subgraph"):
            # Create subgraph for grouped models
            cluster_name = graph.get("cluster_app_name", "cluster_app")
            dot_lines.extend(
                [
                    f"  subgraph {cluster_name} {{",
                    f"    label = {graph.get('name', 'App')}",
                    '    style = "rounded,filled"',
                    '    fillcolor = "#eeeeee"',
                    '    color = "#cccccc"',
                    "",
                ]
            )
            indent = "    "
        else:
            indent = "  "

        # Add model nodes
        for model in graph.get("models", []):
            model_name = model.get("name", "Model")
            label_parts = [f"{model_name}"]

            # Add fields if not disabled
            if not graph_data.get("disable_fields") and model.get("fields"):
                field_lines = []
                for field in model["fields"]:
                    field_name = field.get("label", field.get("name", "field"))
                    field_type = field.get("type", "")

                    # Mark primary key fields
                    if field.get("primary_key"):
                        field_name = f"*{field_name}"

                    # Mark abstract fields
                    if field.get("abstract") and not graph_data.get(
                        "disable_abstract_fields"
                    ):
                        field_name = f"({field_name})"

                    field_line = f"{field_name}: {field_type}"
                    field_lines.append(field_line)

                if field_lines:
                    label_parts.append("|" + "\\l".join(field_lines) + "\\l")

            # Create node label
            label = "{" + "".join(label_parts) + "}"

            # Node styling
            node_attrs = [
                'shape = "record"',
                f'label = "{label}"',
                'fontname = "Helvetica"',
                "fontsize = 8",
            ]

            dot_lines.append(f"{indent}{model_name} [{', '.join(node_attrs)}];")

        dot_lines.append("")

        # Add external model nodes (for models referenced but not included in the graph)
        external_targets = set()
        for model in graph.get("models", []):
            for relation in model.get("relations", []):
                if relation.get("external_target", False):
                    # Only add external targets that weren't filtered out
                    external_targets.add(relation.get("target"))

        for external_target in sorted(external_targets):
            # Create a simple external node with different styling
            node_attrs = [
                'shape = "ellipse"',
                f'label = "{external_target}"',
                'fontname = "Helvetica"',
                "fontsize = 8",
                'style = "filled"',
                'fillcolor = "#f0f0f0"',
                'color = "#999999"',
            ]
            dot_lines.append(f"{indent}{external_target} [{', '.join(node_attrs)}];")

        if external_targets:
            dot_lines.append("")

        # Add relationships
        for model in graph.get("models", []):
            model_name = model.get("name", "Model")

            for relation in model.get("relations", []):
                target = relation.get("target")
                if not target or relation.get("needs_node", True):
                    continue

                label = relation.get("label", "")
                arrows = relation.get("arrows", "")

                # Clean up arrows format
                if arrows.startswith("[") and arrows.endswith("]"):
                    arrows = arrows[1:-1]

                edge_attrs = []
                if arrows:
                    edge_attrs.append(arrows)
                if label and not graph_data.get("hide_edge_labels", False):
                    edge_attrs.append(f'label = "{label}"')
                edge_attrs.append("fontsize = 7")

                edge_attr_str = f" [{', '.join(edge_attrs)}]" if edge_attrs else ""
                dot_lines.append(f"{indent}{model_name} -> {target}{edge_attr_str};")

        if graph_data.get("use_subgraph"):
            dot_lines.append("  }")

        dot_lines.append("")

    dot_lines.append("}")
    return "\n".join(dot_lines)


def render_output_pygraphviz(dotdata, output_file, layout="dot"):
    """Render model data as image using pygraphviz"""
    if not HAS_PYGRAPHVIZ:
        raise ImproperlyConfigured("You need to install pygraphviz python module")

    version = pygraphviz.__version__.rstrip("-svn")
    try:
        if tuple(int(v) for v in version.split(".")) < (0, 36):
            tmpfile = tempfile.NamedTemporaryFile()
            tmpfile.write(dotdata.encode())
            tmpfile.seek(0)
            dotdata = tmpfile.name
    except ValueError:
        pass

    graph = pygraphviz.AGraph(dotdata)
    graph.layout(prog=layout)
    graph.draw(output_file)


def render_output_pydot(dotdata, output_file):
    """Render model data as image using pydot"""
    if not HAS_PYDOT:
        raise ImproperlyConfigured("You need to install pydot python module")

    graph = pydot.graph_from_dot_data(dotdata)
    if not graph:
        raise ValueError("pydot returned an error")
    if isinstance(graph, (list, tuple)) and len(graph) > 0:
        if len(graph) > 1:
            print("Found more than one graph, rendering only the first one.")
        graph = graph[0]
    elif isinstance(graph, (list, tuple)) and len(graph) == 0:
        raise ValueError("pydot returned an empty graph list")

    formats = [
        "bmp",
        "canon",
        "cmap",
        "cmapx",
        "cmapx_np",
        "dot",
        "dia",
        "emf",
        "em",
        "fplus",
        "eps",
        "fig",
        "gd",
        "gd2",
        "gif",
        "gv",
        "imap",
        "imap_np",
        "ismap",
        "jpe",
        "jpeg",
        "jpg",
        "metafile",
        "pdf",
        "pic",
        "plain",
        "plain-ext",
        "png",
        "pov",
        "ps",
        "ps2",
        "svg",
        "svgz",
        "tif",
        "tiff",
        "tk",
        "vml",
        "vmlz",
        "vrml",
        "wbmp",
        "webp",
        "xdot",
    ]
    ext = output_file[output_file.rfind(".") + 1 :]
    format_ = ext if ext in formats else "raw"

    # Ensure we have a valid graph object before calling write
    if hasattr(graph, "write") and callable(getattr(graph, "write", None)):
        graph.write(output_file, format=format_)  # type: ignore
    else:
        raise ValueError("Invalid graph object returned by pydot")


def retheme(graph_data: dict, app_style_filename: str):
    """Apply custom theming to graph data"""
    with open(app_style_filename, "rt") as f:
        app_style = json.load(f, object_pairs_hook=OrderedDict)

    for gc in graph_data["graphs"]:
        for g in gc:
            if "name" in g:
                for m in g["models"]:
                    app_name = g["app_name"]
                    for pattern, style in app_style.items():
                        if fnmatch.fnmatchcase(app_name, pattern):
                            m["style"] = dict(style)
    return graph_data
