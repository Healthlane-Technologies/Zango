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
        "mode": requirement.mode or None,
        "flags": _with_sections(requirement.spec_flags or [], sections),
        "open_decisions": requirement.open_decisions or [],
        "documents": _documents(requirement),
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
    if requirement.open_decisions:
        return 409, {
            "message": "Answer the open decisions on the Review tab before approving.",
            "open_decisions": requirement.open_decisions,
        }
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


# ---------------------------------------------------------------------------
# Manual edits (PUT / PATCH / finalize). Each returns (http_status, payload).
# ---------------------------------------------------------------------------


def _edit_blocked(requirement, base_revision):
    from .models import RequirementStatus

    if requirement.status == RequirementStatus.APPROVED:
        return 409, {
            "message": "This requirement is already approved.",
            "current": spec_payload(requirement),
        }
    if requirement.is_thinking:
        return 409, {
            "message": "The agent is editing this spec right now. Try again when it has replied.",
            "current": spec_payload(requirement),
        }
    try:
        base = int(base_revision)
    except (TypeError, ValueError):
        return 400, {"message": "base_revision is required."}
    if base != requirement.draft_revision:
        return 409, {
            "message": "The spec changed since you started editing.",
            "current": spec_payload(requirement),
        }
    template = requirement.template if requirement.template_slug else None
    if template is None or not template.is_yaml:
        return 400, {"message": "This requirement is not built on a YAML template."}
    return None


def save_manual(requirement, text: str, base_revision):
    """The user saved the whole YAML. Structural errors refuse it; the rest is reported."""
    from zango.apps.shared.app_templates.services.spec.validate import (
        structural_errors,
        validate_text,
    )

    from .models import SpecSource

    blocked = _edit_blocked(requirement, base_revision)
    if blocked:
        return blocked
    text = (text or "").strip()
    if not text:
        return 400, {"message": "The spec is empty."}
    _, issues = validate_text(text, requirement.template)
    broken = structural_errors(issues)
    if broken:
        return 400, {"message": "The spec does not fit the template.", "issues": broken}

    previous = requirement.spec_markdown
    if requirement.spec_is_draft:
        requirement.spec_markdown = text
    else:
        # A finished spec edited by hand is a new agreed revision.
        requirement.record_spec(text, source=SpecSource.USER)
    requirement.draft_revision += 1
    analyse(requirement, previous)
    drop_flags_for(requirement, requirement.changed_paths)
    requirement.save()
    return 200, spec_payload(requirement)


def patch_manual(requirement, ops, base_revision):
    """Apply [{op, path, value?, from?, index?}] to the stored YAML, keeping comments."""
    from zango.apps.shared.app_templates.services.spec import document, yamlio

    blocked = _edit_blocked(requirement, base_revision)
    if blocked:
        return blocked
    if not isinstance(ops, list) or not ops:
        return 400, {"message": "ops must be a non-empty list."}
    try:
        doc = yamlio.load_rt(requirement.spec_markdown or "") or {}
        for op in ops:
            kind = (op or {}).get("op")
            if kind == "set":
                doc, _ = document.set_at(doc, op["path"], op.get("value"))
            elif kind == "add":
                doc, _ = document.add_at(
                    doc, op["path"], op.get("value"), op.get("index")
                )
            elif kind == "remove":
                doc, _ = document.remove_at(doc, op["path"])
            elif kind == "move":
                doc, _ = document.move_at(doc, op["from"], op["path"], op.get("index"))
            else:
                return 400, {"message": f"Unknown op {kind!r}."}
    except (document.PathError, yamlio.SpecYAMLError, KeyError) as exc:
        return 400, {"message": f"Could not apply the change: {exc}"}
    return save_manual(requirement, yamlio.dump_rt(doc), base_revision)


def finalize(requirement, base_revision):
    """The user says the spec is complete: strict checks, then it stops being a draft."""
    from zango.apps.shared.app_templates.services.spec.validate import (
        has_errors,
        validate_text,
    )

    from .models import RequirementStatus, SpecSource

    blocked = _edit_blocked(requirement, base_revision)
    if blocked:
        return blocked
    _, issues = validate_text(
        requirement.spec_markdown, requirement.template, strict=True
    )
    if has_errors(issues):
        return 400, {
            "message": "Fix the problems in the spec first.",
            "issues": [i for i in issues if i["level"] == "error"],
        }
    requirement.record_spec(requirement.spec_markdown, source=SpecSource.USER)
    if requirement.status == RequirementStatus.GATHERING:
        requirement.status = RequirementStatus.READY
    requirement.draft_revision += 1
    requirement.validation_issues = issues
    requirement.save()
    return 200, spec_payload(requirement)


def _with_sections(flags, sections) -> list:
    from zango.apps.shared.app_templates.services.spec.document import section_for

    return [
        {**f, "section": f.get("section") or section_for(f.get("path", ""), sections)}
        for f in flags
    ]


def _documents(requirement) -> list:
    from .documents import document_list

    if requirement.pk is None:
        return []
    return document_list(requirement.documents.all().defer("data", "extracted_text"))


def _covers(changed: str, flagged: str) -> bool:
    return (
        flagged == changed
        or flagged.startswith(changed + "/")
        or changed.startswith(flagged + "/")
    )


def drop_flags_for(requirement, changed_paths) -> None:
    """A path the user edited by hand is no longer an assumption."""
    changed = [p for p in changed_paths or [] if p is not None]
    if not changed or not requirement.spec_flags:
        return
    requirement.spec_flags = [
        f
        for f in requirement.spec_flags
        if not any(_covers(c, f.get("path", "")) for c in changed)
    ]


def confirm_flags(requirement, paths):
    """The user confirmed these assumptions: drop their flags."""
    if not isinstance(paths, list) or not paths:
        return 400, {"message": "paths must be a non-empty list."}
    wanted = {str(p) for p in paths}
    requirement.spec_flags = [
        f for f in requirement.spec_flags or [] if f.get("path") not in wanted
    ]
    requirement.save(update_fields=["spec_flags", "modified_at"])
    return 200, spec_payload(requirement)


def decisions_message(content: str, answers) -> tuple[str, list]:
    """The chat message for answered decisions, and the ids answered."""
    lines, ids = [], []
    for a in answers or []:
        if not isinstance(a, dict) or not str(a.get("answer") or "").strip():
            continue
        ids.append(str(a.get("id") or ""))
        where = f" ({a['path']})" if a.get("path") else ""
        lines.append(
            f"- {a.get('question') or a.get('id')}{where}: {str(a['answer']).strip()}"
        )
    body = (content or "").strip()
    if lines:
        body = (
            (body + "\n\n" if body else "")
            + "My answers to the open decisions:\n"
            + "\n".join(lines)
        )
    return body, ids
