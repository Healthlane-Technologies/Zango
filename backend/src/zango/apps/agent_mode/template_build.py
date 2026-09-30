"""Getting a template requirement's build ready: engine, spec file, skill.

Before the build agent starts on an app built from a template:

* the template's engine paths are restored from the workspace zip, so an edit
  to the engine (by hand or by an earlier run) never reaches the build;
* the approved journey is written to a file in the run directory — specs of
  real programs run past the inline prompt limit, and a file is also what the
  build skill is written to read;
* the build uses the template's own skill, loaded from its materialised
  plugin, alongside the general app-developer skill.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass, field
from pathlib import Path


logger = logging.getLogger("zango.agent_mode")


@dataclass
class TemplateBuild:
    template: object  # catalogue TemplateView
    spec_path: str
    restored: list = field(default_factory=list)  # [(path, "missing"|"changed")]

    @property
    def skill(self) -> str:
        return self.template.qualified_skill

    @property
    def plugin_dir(self) -> str:
        return self.template.plugin_dir

    @property
    def spec_dir(self) -> str:
        return str(Path(self.spec_path).parent)


def prepare(run, workspace_path: str, run_dir: str):
    """A TemplateBuild for ``run``, or None when it is not a YAML template build."""
    from zango.apps.shared.app_templates.models import AppTemplateVersion
    from zango.apps.shared.app_templates.services.workspace import restore_engine

    requirement = getattr(run, "requirement", None)
    if requirement is None or not requirement.template_slug:
        return None
    template = requirement.template
    if template is None or not template.is_yaml:
        return None

    restored = []
    version = AppTemplateVersion.objects.filter(
        object_uuid=template.version_uuid
    ).first()
    if version is not None and version.has_workspace:
        restored = restore_engine(version, Path(workspace_path))

    spec_dir = Path(run_dir) / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / f"{template.spec_root or 'spec'}.yaml"
    spec_path.write_text(requirement.spec_markdown.rstrip() + "\n", encoding="utf-8")
    return TemplateBuild(template=template, spec_path=str(spec_path), restored=restored)
