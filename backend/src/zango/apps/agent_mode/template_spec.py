"""Validation and change tracking for template requirement specs.

Called whenever a template requirement's spec changes — an analyst turn or a
manual save — so ``validation_issues`` and ``changed_paths`` always describe
the spec on screen. Specs of from-scratch (Markdown) requirements are left
alone.
"""

from __future__ import annotations

import logging


logger = logging.getLogger("zango.agent_mode")


def _parse(text):
    from zango.apps.shared.app_templates.services.spec import yamlio

    if not (text or "").strip():
        return None
    try:
        return yamlio.load(text)
    except yamlio.SpecYAMLError:
        return None


def analyse(requirement, previous_text: str | None = None) -> None:
    """Refresh ``validation_issues`` (and ``changed_paths`` if the spec moved).

    ``previous_text`` is the spec before the change; pass None to leave the
    changed paths as they are (a re-validation, not a change).
    """
    from zango.apps.shared.app_templates.services.spec.document import diff
    from zango.apps.shared.app_templates.services.spec.validate import validate_text

    template = requirement.template if requirement.template_slug else None
    if template is None or not template.is_yaml:
        return
    text = requirement.spec_markdown or ""
    try:
        doc, issues = validate_text(text, template)
    except Exception:  # noqa: BLE001
        logger.exception("agent_mode: validating %s failed", requirement.pk)
        return
    requirement.validation_issues = issues
    if previous_text is not None and text.strip() != (previous_text or "").strip():
        old = _parse(previous_text)
        requirement.changed_paths = (
            diff(old, doc) if old is not None and doc is not None else [""]
        )


def spec_payload(requirement) -> dict:
    """What the console's builder panel reads for a requirement's spec."""
    template = requirement.template if requirement.template_slug else None
    sections = (template.ui_schema or {}).get("sections", []) if template else []
    return {
        "text": requirement.spec_markdown,
        "format": requirement.spec_format,
        "status": requirement.status,
        "spec_version": requirement.spec_version,
        "draft_revision": requirement.draft_revision,
        "is_draft": requirement.spec_is_draft,
        "issues": requirement.validation_issues or [],
        "changed_paths": requirement.changed_paths or [],
        "sections": [
            {"id": s.get("id"), "title": s.get("title", "")} for s in sections
        ],
        "template": (
            {
                "slug": template.slug,
                "name": template.name,
                "version": template.version,
                "version_uuid": template.version_uuid,
            }
            if template
            else None
        ),
    }


def approval_problem(requirement):
    """Why ``requirement`` cannot be approved, as (http_status, payload), or None."""
    if not (requirement.spec_markdown or "").strip():
        return 400, {"message": "There is no specification to approve yet."}
    if requirement.is_thinking:
        return 409, {"message": "The agent is still working on this spec."}
    template = requirement.template if requirement.template_slug else None
    if template is None or not template.is_yaml:
        return None
    from zango.apps.shared.app_templates.services.spec.validate import (
        has_errors,
        validate_text,
    )

    if requirement.spec_is_draft:
        return 409, {
            "message": "The spec is still a draft. Finish the interview, or save it yourself, first."
        }
    _, issues = validate_text(requirement.spec_markdown, template, strict=True)
    if has_errors(issues):
        return 400, {
            "message": "Fix the problems in the spec before approving it.",
            "issues": [i for i in issues if i["level"] == "error"],
        }
    return None
