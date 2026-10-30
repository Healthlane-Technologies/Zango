"""Getting a template requirement's build ready: engine, spec file, skill.

Before the build agent starts on an app built from a template:

* the template's engine paths are restored from the workspace zip, so an edit
  to the engine (by hand or by an earlier run) never reaches the build;
* the approved journey is written to a file in the run directory — specs of
  real programs run past the inline prompt limit, and a file is also what the
  build skill is written to read;
* the build uses the template's skill: App Studio from Agent Mode's plugin
  for every template on the generic spec, or the template's own (PSP's),
  which is loaded beside the general app-developer skill it relies on.
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
        """The template's own materialised pack (its requirement documents)."""
        return self.template.plugin_dir

    @property
    def skill_plugin_dir(self) -> str:
        """The plugin the build skill comes from (Agent Mode's for App Studio)."""
        return self.template.build_plugin_dir

    @property
    def skill_dir(self) -> str:
        """The build skill's own directory, or "" without one."""
        name = self.template.build_skill_name
        return str(Path(self.skill_plugin_dir) / "skills" / name) if name else ""

    @property
    def spec_dir(self) -> str:
        return str(Path(self.spec_path).parent)


class PinMismatch(Exception):
    """The approved version's prototype does not match the hash it was approved with."""


@dataclass
class Approved:
    """What a build builds: the approved version, never the live requirement (G1)."""

    spec: str
    preview_mode: str
    prototype: dict
    prototype_hash: str
    version: object = (
        None  # AgentRequirementVersion, or None for a run from before pinning
    )
    baseline: str = ""

    @property
    def is_open(self) -> bool:
        return self.preview_mode == "open" and bool(self.prototype)


def approved(run) -> Approved | None:
    """The spec, preview mode and prototype ``run`` builds.

    A run pinned to a version (``run.requirement_version``, set when the build is started) reads
    that version only, so editing the requirement after Commit (another chat turn, a second tab)
    cannot change what is built. A run from before pinning reads the requirement as it is.
    Raises PinMismatch when the version's prototype is not the one it was approved with.
    """
    requirement = getattr(run, "requirement", None)
    version = getattr(run, "requirement_version", None)
    if version is not None:
        from .prototype import parts_hash

        parts = dict(version.prototype_parts or {})
        if (
            parts
            and version.prototype_hash
            and parts_hash(parts) != version.prototype_hash
        ):
            raise PinMismatch(
                f"Requirement version {version.version}: the prototype does not match its hash."
            )
        return Approved(
            spec=version.spec_markdown or "",
            # A version recorded before preview_mode was kept follows the requirement's.
            preview_mode=version.preview_mode
            or (getattr(requirement, "preview_mode", "") or "kit"),
            prototype=parts,
            prototype_hash=version.prototype_hash or "",
            version=version,
            baseline=version.baseline or "",
        )
    if requirement is None:
        return None
    return Approved(
        spec=requirement.spec_markdown or "",
        preview_mode=requirement.preview_mode or "kit",
        prototype=dict(requirement.prototype_parts or {}),
        prototype_hash=requirement.prototype_hash or "",
    )


def pin_version(requirement):
    """The version a build of ``requirement`` started now should be pinned to: its newest agreed
    (non-draft) version when it is approved, else None."""
    from .models import RequirementStatus

    if requirement is None or requirement.status != RequirementStatus.APPROVED:
        return None
    return requirement.versions.filter(is_draft=False).order_by("-version").first()


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
    pinned = approved(run)
    spec_path.write_text(
        (pinned.spec if pinned else requirement.spec_markdown).rstrip() + "\n",
        encoding="utf-8",
    )
    return TemplateBuild(template=template, spec_path=str(spec_path), restored=restored)
