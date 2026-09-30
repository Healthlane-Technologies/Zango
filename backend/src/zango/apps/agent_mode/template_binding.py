"""Tie an app to the template it is built on, and start its requirements there.

An app created from a template is *bound* to one version of it
(``AppTemplateBinding``, public schema). Every requirement on that app — the
first one and every change request after it — is a template requirement on
that version: its spec is the template's YAML, and it starts as a draft the
analyst fills in, never as an empty page.

Where a change request starts from matters. The first requirement starts from
the template's starter journey; a later one starts from the spec the app was
last approved on, because a change request amends the running program rather
than re-describing it from scratch.
"""

from __future__ import annotations

import logging


logger = logging.getLogger("zango.agent_mode")


def binding_for(tenant):
    """The app's template binding, or None. Safe from a tenant schema."""
    from zango.apps.shared.app_templates.models import AppTemplateBinding

    if tenant is None:
        return None
    return (
        AppTemplateBinding.objects.select_related("template", "version")
        .filter(tenant_id=tenant.pk)
        .first()
    )


def bind_app(tenant, version, source: str):
    """Bind ``tenant`` to ``version`` if it is not bound yet; return the binding.

    An existing binding is kept as it is: moving an app to a newer version is
    an explicit upgrade, never a side effect of starting a conversation.
    """
    from zango.apps.shared.app_templates.models import AppTemplateBinding

    binding, created = AppTemplateBinding.objects.get_or_create(
        tenant_id=tenant.pk,
        defaults={"template": version.template, "version": version, "source": source},
    )
    if created:
        logger.info(
            "agent_mode: bound app %s to template %s@%s",
            tenant.name,
            version.template.slug,
            version.version,
        )
    return binding


def last_approved_spec(template_slug: str) -> str:
    """The most recently approved spec on this template, in the current schema."""
    from .models import AgentRequirement, RequirementStatus

    previous = (
        AgentRequirement.objects.filter(
            template_slug=template_slug, status=RequirementStatus.APPROVED
        )
        .exclude(spec_markdown="")
        .order_by("-approved_at", "-created_at")
        .first()
    )
    return previous.spec_markdown if previous else ""


def seed_template_requirement(requirement, template, base_spec: str = "") -> None:
    """Make an unsaved/new requirement a template one, with a draft to work on.

    ``template`` is a catalogue TemplateView. The draft is ``base_spec`` when
    given (a change request), otherwise the template's starter journey.
    """
    requirement.adopt_template(template.slug, version_uuid=template.version_uuid)
    spec = (base_spec or template.starter_yaml or "").strip()
    if spec:
        requirement.spec_markdown = spec
        requirement.spec_is_draft = True
        requirement.draft_revision = max(requirement.draft_revision, 1)

    from .template_spec import analyse

    analyse(requirement)


def seed_from_binding(requirement, tenant) -> bool:
    """For a requirement on a bound app: pin the binding's version and seed it.

    Runs inside the tenant schema. Returns whether the app is bound.
    """
    from .app_templates import get_template

    binding = binding_for(tenant)
    if binding is None:
        return False
    template = get_template(
        binding.template.slug, version_uuid=binding.version.object_uuid
    )
    if template is None:
        logger.warning(
            "agent_mode: %s is bound to a template that no longer loads", tenant.name
        )
        return False
    seed_template_requirement(requirement, template, last_approved_spec(template.slug))
    return True
