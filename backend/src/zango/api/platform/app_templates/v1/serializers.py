"""Catalogue payloads for the console's template gallery and detail page."""

from __future__ import annotations

from django.db.models import Count


def apps_using_counts() -> dict:
    """template id -> number of apps bound to it."""
    from zango.apps.shared.app_templates.models import AppTemplateBinding

    rows = AppTemplateBinding.objects.values("template_id").annotate(n=Count("id"))
    return {row["template_id"]: row["n"] for row in rows}


def template_summary(template, version, apps_using: int = 0) -> dict:
    catalogue = version.catalogue or {}
    return {
        "slug": template.slug,
        "name": template.name,
        "category": template.category,
        "icon": template.icon,
        "one_liner": template.one_liner,
        "is_beta": template.is_beta,
        "version": version.version,
        "version_uuid": str(version.object_uuid),
        "published_at": version.published_at.isoformat()
        if version.published_at
        else None,
        "apps_using": apps_using,
        "spec_format": version.spec_format,
        "catalogue": {
            "description": catalogue.get("description", ""),
            "aka": catalogue.get("aka", []),
            "fits_when": catalogue.get("fits_when", []),
            "gives_you": catalogue.get("gives_you", []),
            "packages": catalogue.get("packages", []),
            "roles": catalogue.get("roles", []),
            "workflows": catalogue.get("workflows", []),
            "data_objects": catalogue.get("data_objects", []),
            "integrations": catalogue.get("integrations", []),
            "compliance": catalogue.get("compliance", []),
            "recommended_agents": catalogue.get("recommended_agents", []),
            "app_name_prefill": catalogue.get("app_name_prefill", ""),
            "app_prompt_prefill": catalogue.get("app_prompt_prefill", ""),
        },
        "sections": [
            {"id": s["id"], "title": s.get("title", ""), "hint": s.get("hint", "")}
            for s in version.sections
        ],
    }


def template_detail(template, version, apps_using: int = 0) -> dict:
    from zango.apps.shared.app_templates.models import VersionStatus

    data = template_summary(template, version, apps_using)
    data["versions"] = [
        {
            "version": v.version,
            "status": v.status,
            "published_at": v.published_at.isoformat() if v.published_at else None,
            "changelog": v.changelog,
        }
        for v in template.versions.exclude(status=VersionStatus.DRAFT).order_by(
            "-published_at"
        )
    ]
    data["starter_yaml"] = version.starter_yaml
    data["example_yaml"] = version.example_yaml
    return data


def app_template_ref(tenant) -> dict | None:
    """What an app payload says about its template, or None."""
    binding = getattr(tenant, "template_binding", None)
    if binding is None:
        return None
    return {
        "slug": binding.template.slug,
        "name": binding.template.name,
        "version": binding.version.version,
    }
