"""Validate a requirement spec against its template: YAML, JSON Schema, rules.

Issues are ``{level, path, message, code, section, rule?, line?}`` with
concrete JSON Pointers, so the console can put each one on a field.

Schema errors come in two kinds, and they are treated differently:

* **structural** — the wrong type, an unknown value, a shape the template does
  not have. Always an error: a change that introduces one is refused.
* **completeness** — something required is still missing. Mid-interview that
  is expected, so it is a warning; at finalize (``strict=True``) it is an error.
"""

from __future__ import annotations

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from . import rules as rules_mod
from . import yamlio
from .document import section_for, to_pointer


COMPLETENESS = {
    "required",
    "minItems",
    "minProperties",
    "minLength",
    "dependentRequired",
}

_validators: dict = {}


def _validator(schema: dict):
    key = id(schema)
    validator = _validators.get(key)
    if validator is None or validator.schema is not schema:
        validator = _validators[key] = Draft202012Validator(schema)
    return validator


def _message(error) -> str:
    # {"not": {"required": [key]}}: a key that is only allowed in another shape.
    forbidden = (error.validator_value or {}).get("required") if error.validator == "not" and isinstance(error.validator_value, dict) else None
    if forbidden:
        return f"{', '.join(forbidden)} is not allowed here."
    if error.validator in ("anyOf", "oneOf") and error.context:
        inner = best_match(error.context)
        if inner is not None:
            return inner.message
    return error.message


def schema_issues(doc, schema: dict, *, strict: bool = False) -> list:
    if not schema:
        return []
    issues = []
    for error in _validator(schema).iter_errors(doc):
        complete = error.validator in COMPLETENESS
        issues.append(
            {
                "level": "error" if (strict or not complete) else "warning",
                "path": to_pointer(error.absolute_path),
                "message": _message(error),
                "code": f"schema:{error.validator}",
                "structural": not complete,
            }
        )
    return issues


def validate_doc(doc, template, *, strict: bool = False) -> list:
    """Issues for an already-parsed document against a TemplateView."""
    issues = schema_issues(doc, template.json_schema, strict=strict)
    # Rule breaches (a role not declared yet…) are often transient mid-interview:
    # they block finalize and approval, not an individual edit.
    for issue in rules_mod.evaluate(doc, template.rules):
        issue["structural"] = False
        issues.append(issue)
    if getattr(template, "spec_dialect", "") == "zango-app/1":
        issues.extend(_braced_prose(doc))
    # What the build itself will stop on (never blocks an individual edit).
    from .build_check import build_issues

    issues.extend(build_issues(doc, template))
    sections = (template.ui_schema or {}).get("sections") or []
    for issue in issues:
        issue.setdefault("section", section_for(issue["path"], sections))
    order = {"error": 0, "warning": 1}
    issues.sort(key=lambda i: (order.get(i["level"], 2), i["path"]))
    return issues


PROSE_KEYS = {"text", "on_done", "on_create", "computed", "description", "condition_msg", "message"}


def _braced_prose(doc) -> list:
    """Prose written as "{...}": the braces show literally in the app and the build."""
    found = []

    def walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                if (
                    key in PROSE_KEYS
                    and isinstance(value, str)
                    and value.strip().startswith("{")
                    and value.strip().endswith("}")
                ):
                    found.append(
                        {
                            "level": "warning",
                            "path": to_pointer([*path, key]),
                            "message": "This text is wrapped in braces, which show literally. "
                            "Remove the { } — a block scalar (>- or |) needs no quoting.",
                            "code": "prose_braces",
                            "structural": False,
                        }
                    )
                else:
                    walk(value, [*path, key])
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, [*path, i])

    walk(doc, [])
    return found


def validate_text(text: str, template, *, strict: bool = False):
    """(document or None, issues) for spec text against a TemplateView."""
    try:
        doc = yamlio.load(text)
    except yamlio.SpecYAMLError as exc:
        return None, [
            {
                "level": "error",
                "path": "",
                "message": f"The YAML could not be read: {exc}",
                "code": "yaml",
                "structural": True,
                "line": exc.line,
                "section": "",
            }
        ]
    return doc, validate_doc(doc, template, strict=strict)


def has_errors(issues) -> bool:
    return any(i.get("level") == "error" for i in issues or ())


def structural_errors(issues) -> list:
    return [
        i
        for i in issues or ()
        if i.get("level") == "error" and i.get("structural", True)
    ]
