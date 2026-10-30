"""Template mode: an app opened straight on its template's preview, with no brief.

A template whose version says ``launch: "direct"`` (AppTemplateVersion) starts its first
requirement here rather than with a brief and an analyst turn: the spec is the template's starter,
the preview is its stored starting prototype (Free design, ``preview_mode == "open"``), and the chat
opens on a welcome the platform writes. Nothing runs and nothing is spent until the creator asks for
a change; they can Commit the template as it is at revision 1.

Also here: the *baseline* a requirement version's prototype is compared against, for the build's
change map (approval_bundle.write_change_map): the template's starting prototype for the first
requirement, the last approved version for a change request.
"""

from __future__ import annotations

from .models import RequirementStatus


TEMPLATE_MODE = "template"


def is_direct(template) -> bool:
    """Whether a catalogue TemplateView opens as it is (launch direct, with a prototype)."""
    return bool(template is not None and getattr(template, "is_direct", False))


def welcome_text(template) -> str:
    welcome = getattr(template, "welcome", None) or {}
    text = str(welcome.get("message") or "").strip()
    return text or (
        f"This is the {template.name} template, running on demo data. Tell me what to change, "
        "or build it as it is."
    )


def suggestions(template) -> list[str]:
    welcome = getattr(template, "welcome", None) or {}
    return [str(s) for s in welcome.get("suggestions") or [] if str(s).strip()][:6]


def seed_direct(requirement, template) -> None:
    """Make an unsaved requirement a template-mode one: the starter, its prototype, ready.

    ``template`` is a catalogue TemplateView with ``is_direct``. The spec gets what Free design
    needs next to the prototype (``app.design``, ``prototype.screens``: prototype_kit.open_spec),
    so the coverage gate passes and Commit works before any edit.
    """
    from .prototype_kit import open_spec
    from .template_spec import analyse

    parts = dict(template.prototype_parts or {})
    requirement.adopt_template(template.slug, version_uuid=template.version_uuid)
    requirement.initial_prompt = ""
    requirement.mode = TEMPLATE_MODE
    requirement.preview_mode = "open"
    requirement.prototype_parts = parts
    requirement.prototype_hash = template.prototype_hash
    requirement.prototype_revision = max(requirement.prototype_revision, 1)
    requirement.spec_markdown = open_spec(template.starter_yaml or "", parts).strip()
    requirement.spec_is_draft = True
    requirement.draft_revision = max(requirement.draft_revision, 1)
    requirement.status = RequirementStatus.READY
    requirement.is_thinking = False
    analyse(requirement)


def is_template_mode(requirement) -> bool:
    return getattr(requirement, "mode", "") == TEMPLATE_MODE


# ---------------------------------------------------------------------------
# Baseline: what changed since the last thing the user agreed and we built
# ---------------------------------------------------------------------------


def baseline_for(requirement) -> str:
    """The baseline for ``requirement``'s next version, as a reference string:

    * ``version:<n>``: an earlier version of this requirement that was built;
    * ``requirement:<uuid>:<n>``: a change request's starting point, the app's last approved
      requirement on the same template (its approved version);
    * ``template:<version uuid>``: the template's starting prototype;
    * ``""``: nothing to compare against (every screen is new).
    """
    from .models import AgentRequirement, AgentRequirementVersion

    if requirement.pk is not None:
        built = (
            requirement.versions.filter(is_draft=False, runs__isnull=False)
            .exclude(prototype_hash="")
            .order_by("-version")
            .first()
        )
        if built is not None:
            return f"version:{built.version}"
    if requirement.template_slug:
        previous = (
            AgentRequirement.objects.filter(
                template_slug=requirement.template_slug,
                status=RequirementStatus.APPROVED,
            )
            .exclude(pk=requirement.pk)
            .order_by("-approved_at", "-created_at")
            .first()
        )
        if previous is not None:
            agreed = (
                AgentRequirementVersion.objects.filter(
                    requirement=previous, is_draft=False
                )
                .exclude(prototype_hash="")
                .order_by("-version")
                .first()
            )
            if agreed is not None:
                return f"requirement:{previous.object_uuid}:{agreed.version}"
    template = requirement.template if requirement.template_slug else None
    if template is not None and getattr(template, "prototype_parts", None):
        return f"template:{template.version_uuid}"
    return ""


def baseline_parts(requirement, baseline: str) -> tuple[str, dict]:
    """``(label, parts)`` for a baseline reference (baseline_for); ``("", {})`` when it is
    empty or no longer resolves. The label is what changes.json says it compared against."""
    from .models import AgentRequirementVersion

    kind, _, rest = (baseline or "").partition(":")
    try:
        if kind == "version" and requirement is not None:
            v = requirement.versions.get(version=int(rest), is_draft=False)
            return f"version {v.version}", dict(v.prototype_parts or {})
        if kind == "requirement":
            uuid, _, n = rest.rpartition(":")
            v = AgentRequirementVersion.objects.select_related("requirement").get(
                requirement__object_uuid=uuid, version=int(n), is_draft=False
            )
            return (
                f"approved requirement {v.requirement.title or uuid} version {v.version}",
                dict(v.prototype_parts or {}),
            )
        if kind == "template":
            from .app_templates import get_template

            slug = getattr(requirement, "template_slug", "") if requirement else ""
            template = get_template(slug, version_uuid=rest) if slug else None
            if template is not None:
                return (
                    f"template {template.slug}@{template.version}",
                    dict(template.prototype_parts or {}),
                )
    except (AgentRequirementVersion.DoesNotExist, ValueError):
        pass
    return "", {}
