"""The generic template, and what other templates borrow from it.

Every template is a YAML spec and a preview of the app it describes. Most
templates are written in the generic Zango app spec (``zango-app/1``); one of
those only has to ship what makes it different — usually a starter spec and
its catalogue entry. Whatever it leaves out (the JSON Schema and rules, the
requirement documents the analyst follows, the preview page) comes from the
current version of the generic template, ``zango-app``.

Templates in any other dialect (PSP's journey, say) must be complete: nothing
else can describe or preview their YAML.
"""

from __future__ import annotations

from django.db.models import F


GENERIC_SLUG = "zango-app"
GENERIC_DIALECT = "zango-app/1"

# Requirement-side pieces a template may leave to the generic one: the
# version attribute, and the key its document has in TemplateView.files.
BORROWED_FIELDS = (
    ("json_schema", "json_schema"),
    ("ui_schema", "ui_schema"),
    ("rules", "rules"),
    ("interview_md", "interview"),
    ("schema_md", "schema"),
    ("drafting_md", "drafting"),
)


def generic_version():
    """The generic template's current published version, or None."""
    from ..models import AppTemplateVersion, TemplateStatus, VersionStatus

    return (
        AppTemplateVersion.objects.select_related("template")
        .filter(
            template__slug=GENERIC_SLUG,
            template__status=TemplateStatus.PUBLISHED,
            template__current_version_id=F("pk"),
            status=VersionStatus.PUBLISHED,
        )
        .first()
    )


def borrows(version) -> bool:
    """Whether ``version`` falls back to the generic template."""
    return (
        version.spec_dialect == GENERIC_DIALECT
        and version.template.slug != GENERIC_SLUG
    )


def follow_current(version):
    """The version a requirement on ``version`` actually works with.

    An app pinned to an older version of the generic template itself follows
    its current version — schema, rules, guidance and preview page —
    because those are how a generic spec is written, previewed and
    built, and they only get better. Every other template keeps its pin (a
    template with an engine is built against exactly the version it chose).
    """
    if (
        version is None
        or version.template.slug != GENERIC_SLUG
        or version.spec_dialect != GENERIC_DIALECT
    ):
        return version
    current = generic_version()
    return (
        current
        if current is not None and current.spec_dialect == GENERIC_DIALECT
        else version
    )


# Every spec in the generic dialect is built with the App Studio skill. It
# ships in Agent Mode's own skill plugin rather than in a template pack, so a
# pack (the generic one included) never carries a copy that can drift.
STUDIO_PLUGIN = "zango-agent-mode"
STUDIO_SKILL = "zango-app-studio"


def studio_plugin_dir() -> str:
    """Agent Mode's skill plugin, where the App Studio skill lives."""
    from pathlib import Path

    return str(Path(__file__).resolve().parents[3] / "agent_mode" / "skill_plugin")


def builds_with_studio(version) -> bool:
    """Whether ``version`` is built with the App Studio skill.

    Any version on the generic spec without a build skill of its own is —
    including older versions of the generic template itself, which an app
    may be pinned to and which still name the skill they used to ship.
    """
    if version.spec_dialect != GENERIC_DIALECT:
        return False
    return not version.build_skill_name or version.template.slug == GENERIC_SLUG


def fallback_for(version):
    """The generic version ``version`` borrows from, or None."""
    return generic_version() if borrows(version) else None


def effective(version, field: str, generic=None):
    """``version.<field>``, or the generic template's when it has none."""
    value = getattr(version, field)
    if value:
        return value
    generic = generic if generic is not None else fallback_for(version)
    return getattr(generic, field) if generic is not None else value


def preview_version(version):
    """The version whose page previews ``version``'s spec, and where it came from.

    Returns (version_with_a_page, "template" | "generic") or (None, None).
    """
    if version.has_builder:
        return version, "template"
    generic = fallback_for(version)
    if generic is not None and generic.has_builder:
        return generic, "generic"
    return None, None
