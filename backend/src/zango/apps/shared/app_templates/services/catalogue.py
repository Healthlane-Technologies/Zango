"""Read side of the template catalogue: what agents and APIs look templates up by.

``TemplateView`` keeps the attribute names of the old file-based
``agent_mode.app_templates.AppTemplate`` (slug, name, one_liner, path,
spec_format, spec_root, aka, fits_when, gives_you, sections, files, is_yaml,
file_path) so existing callers keep working, and adds what the database knows
(version, json_schema, rules, build skill…).

Caching:
* a published version never changes, so its view is cached in-process by
  (uuid, content_sha) for the life of the process;
* *which* version is current per slug can change on publish, so that map is
  keyed by a revision number held in the shared Django cache (Redis) and
  bumped by every publish/archive. Workers notice on their next lookup.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass, field
from pathlib import Path

from django.core.cache import cache
from django.db.models import F

from ..models import AppTemplate, AppTemplateVersion, TemplateStatus, VersionStatus
from .materialise import REQUIREMENT_FILES, REQUIREMENTS_DIR, materialise


logger = logging.getLogger("zango.app_templates")

REV_KEY = "app_templates:rev"
MAX_SLUG = 64

_views: dict = {}
_current: dict = {"rev": None, "by_slug": {}}


@dataclass(frozen=True)
class TemplateView:
    slug: str
    name: str
    one_liner: str
    path: str  # materialised requirements dir (what the analyst reads)
    spec_format: str = "markdown"
    spec_root: str = ""
    spec_dialect: str = ""
    aka: tuple = ()
    fits_when: tuple = ()
    gives_you: tuple = ()
    sections: tuple = ()  # ((id, title), ...)
    files: dict = field(default_factory=dict)  # key -> file name in `path`
    # --- from the database
    version: str = ""
    version_uuid: str = ""
    content_sha: str = ""
    category: str = ""
    icon: str = ""
    is_beta: bool = False
    catalogue: dict = field(default_factory=dict)
    json_schema: dict = field(default_factory=dict)
    ui_schema: dict = field(default_factory=dict)
    rules: tuple = ()
    starter_yaml: str = ""
    example_yaml: str = ""
    build_skill_name: str = ""
    plugin_dir: str = ""  # materialised plugin root (for the build agent)
    references: tuple = ()  # ({id, title, summary, tags, path}, ...)
    borrowed_from: str = (
        ""  # "zango-app@1.0.0" when pieces come from the generic template
    )
    # Where the build skill lives when it is not the template's own: App Studio,
    # from Agent Mode's skill plugin (see generic.py).
    skill_plugin_name: str = ""
    skill_plugin_dir: str = ""
    # Template mode: "direct" opens on the template's preview with no brief (welcome +
    # its starting prototype, open-mode parts).
    launch: str = "brief"
    welcome: dict = field(default_factory=dict)
    prototype_parts: dict = field(default_factory=dict)
    prototype_hash: str = ""

    @property
    def is_direct(self) -> bool:
        return self.launch == "direct" and bool(self.prototype_parts)

    @property
    def is_yaml(self) -> bool:
        return self.spec_format == "yaml"

    def file_path(self, key: str) -> str:
        """Absolute path of one of the pack's documents, or "" if it has none."""
        name = self.files.get(key)
        return str(Path(self.path) / name) if name else ""

    @property
    def qualified_skill(self) -> str:
        """The build skill as Claude Code names it: ``<plugin>:<skill>``."""
        if not self.build_skill_name:
            return ""
        return f"{self.skill_plugin_name or 'zango-tpl-' + self.slug}:{self.build_skill_name}"

    @property
    def build_plugin_dir(self) -> str:
        """The plugin the build skill is loaded from: this template's, or Agent Mode's."""
        return self.skill_plugin_dir or self.plugin_dir


def _strings(value, limit: int = 12) -> tuple:
    if not isinstance(value, list):
        return ()
    return tuple(str(v).strip() for v in value[:limit] if str(v).strip())


def build_view(version: AppTemplateVersion) -> TemplateView:
    """A TemplateView for ``version``, materialising it onto disk first."""
    template = version.template
    plugin_dir = materialise(version)
    req_dir = plugin_dir / REQUIREMENTS_DIR
    files = {
        key: name
        for key, name in REQUIREMENT_FILES.items()
        if (req_dir / name).is_file()
    }
    cat = version.catalogue or {}

    # Pieces the template leaves to the generic one (see generic.py): its
    # documents are read where the generic version is materialised.
    from .generic import BORROWED_FIELDS, fallback_for

    generic = fallback_for(version)
    borrowed = {}
    if generic is not None:
        generic_dir = materialise(generic) / REQUIREMENTS_DIR
        for attr, key in BORROWED_FIELDS:
            if getattr(version, attr) or key in files:
                continue
            name = REQUIREMENT_FILES[key]
            if (generic_dir / name).is_file():
                files[key] = str(generic_dir / name)
                borrowed[attr] = getattr(generic, attr)
    from .generic import (
        STUDIO_PLUGIN,
        STUDIO_SKILL,
        builds_with_studio,
        studio_plugin_dir,
    )

    studio = builds_with_studio(version)
    return TemplateView(
        slug=template.slug,
        name=template.name,
        one_liner=template.one_liner,
        path=str(req_dir),
        spec_format=version.spec_format,
        spec_root=version.spec_root,
        spec_dialect=version.spec_dialect,
        aka=_strings(cat.get("aka"), 8),
        fits_when=_strings(cat.get("fits_when")),
        gives_you=_strings(cat.get("gives_you")),
        sections=tuple(
            (s["id"], s.get("title", ""))
            for s in (
                generic.sections
                if "ui_schema" in borrowed and not version.sections
                else version.sections
            )
        ),
        files=files,
        version=version.version,
        version_uuid=str(version.object_uuid),
        content_sha=version.content_sha,
        category=template.category,
        icon=template.icon,
        is_beta=template.is_beta,
        catalogue=cat,
        json_schema=version.json_schema or borrowed.get("json_schema") or {},
        ui_schema=version.ui_schema or borrowed.get("ui_schema") or {},
        rules=tuple(version.rules or borrowed.get("rules") or ()),
        starter_yaml=version.starter_yaml,
        example_yaml=version.example_yaml,
        build_skill_name=STUDIO_SKILL if studio else version.build_skill_name,
        skill_plugin_name=STUDIO_PLUGIN if studio else "",
        skill_plugin_dir=studio_plugin_dir() if studio else "",
        plugin_dir=str(plugin_dir),
        references=tuple(
            {
                "id": r["id"],
                "title": r.get("title", r["id"]),
                "summary": r.get("summary", ""),
                "tags": list(r.get("tags") or []),
                "path": str(req_dir / "references" / f"{r['id']}.yaml"),
            }
            for r in version.references or []
        ),
        borrowed_from=(
            f"{generic.template.slug}@{generic.version}" if borrowed else ""
        ),
        launch=version.launch or "brief",
        welcome=dict(version.welcome or {}),
        prototype_parts=dict(version.prototype_parts or {}),
        prototype_hash=version.prototype_hash or "",
    )


def bump_revision() -> None:
    """Tell every worker the current-version map changed (publish, archive…)."""
    try:
        cache.incr(REV_KEY)
    except ValueError:
        cache.set(REV_KEY, 1, timeout=None)
    _current["rev"] = None


def clear_caches() -> None:
    """Forget everything cached in this process (tests, management commands)."""
    _views.clear()
    _current["rev"] = None
    _current["by_slug"] = {}


def _view_for(version: AppTemplateVersion) -> TemplateView:
    if version.is_draft:
        return build_view(version)  # drafts change; never cache them
    key = (version.object_uuid, version.content_sha)
    if version.spec_dialect:
        # What it borrows follows the generic template's current version.
        from .generic import generic_version

        generic = generic_version()
        key += (generic.content_sha if generic is not None else "",)
    view = _views.get(key)
    if view is None:
        view = _views[key] = build_view(version)
    return view


def _current_versions() -> dict:
    """slug -> TemplateView of its current published version."""
    rev = cache.get(REV_KEY, 0)
    if _current["rev"] == rev:
        return _current["by_slug"]
    by_slug = {}
    versions = (
        AppTemplateVersion.objects.select_related("template")
        .filter(
            template__status=TemplateStatus.PUBLISHED,
            template__current_version_id=F("pk"),
            status=VersionStatus.PUBLISHED,
        )
        .order_by("template__sort_order", "template__name")
    )
    for version in versions:
        try:
            by_slug[version.template.slug] = _view_for(version)
        except Exception:
            logger.exception("app_templates: could not load %s", version)
    _current.update(rev=rev, by_slug=by_slug)
    return by_slug


def _clean_slug(slug) -> str:
    return str(slug or "").strip().lower()[:MAX_SLUG]


def load_templates() -> dict:
    """Every published template, keyed by slug, in gallery order."""
    return dict(_current_versions())


def get_template(slug, version_uuid=None):
    """A template by slug — its current version, or a pinned one — or None.

    Safe to call with user or model input. A pinned version resolves even if
    the template has since moved on or been archived: the app was built on it.
    """
    slug = _clean_slug(slug)
    if not slug:
        return None
    if version_uuid:
        version = (
            AppTemplateVersion.objects.select_related("template")
            .filter(object_uuid=version_uuid, template__slug=slug)
            .first()
        )
        from .generic import follow_current

        version = follow_current(version)
        return _view_for(version) if version else None
    return _current_versions().get(slug)


def unlisted_slugs() -> set:
    """Templates left out of the gallery and the analyst's offers (``AppTemplate.listed``).

    Read from the database each time, not from the cached views: listing is the
    template's, not the version's, so it changes without a new version. The
    generic template is never in it — it starts every app described from scratch.
    """
    from .generic import GENERIC_SLUG

    return set(
        AppTemplate.objects.filter(listed=False)
        .exclude(slug=GENERIC_SLUG)
        .values_list("slug", flat=True)
    )


def spec_format_for(slug) -> str:
    template = get_template(slug)
    return template.spec_format if template else "markdown"


def catalogue_digest() -> str:
    """What the analyst is told about the templates, on its first turn.

    Enough to decide whether to offer one and to describe it convincingly,
    and nothing more: the pack itself is only opened once the user says yes,
    so a declined offer costs a few hundred tokens rather than a file read.
    """
    templates = load_templates()
    hidden = unlisted_slugs()
    templates = {slug: t for slug, t in templates.items() if slug not in hidden}
    if not templates:
        return ""

    blocks = []
    for template in templates.values():
        lines = [f"### {template.name}  (slug: {template.slug})"]
        if template.aka:
            lines.append(f"also called: {', '.join(template.aka)}")
        lines.append(template.one_liner)
        if template.fits_when:
            lines.append("Offer it when:")
            lines.extend(f"  - {item}" for item in template.fits_when)
        if template.gives_you:
            lines.append("Already built:")
            lines.extend(f"  - {item}" for item in template.gives_you)
        lines.append(f"pack: {template.path}/")
        lines.append(
            f"spec format: {template.spec_format}"
            + (f" (root key `{template.spec_root}`)" if template.spec_root else "")
        )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
