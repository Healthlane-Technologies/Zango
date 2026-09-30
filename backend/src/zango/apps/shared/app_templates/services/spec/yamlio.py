"""YAML in and out of requirement specs.

Specs are YAML 1.2, read with ruamel. PyYAML speaks YAML 1.1, where a bare
``on:``/``yes:``/``no:`` key is a boolean — PSP writes ``notify_client.on:``,
which PyYAML turns into ``True:`` and the schema then rejects. Always parse
specs here, never with ``yaml.safe_load``.
"""

from __future__ import annotations

import io

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError


MAX_SPEC_BYTES = 256 * 1024


class SpecYAMLError(ValueError):
    """The text is not usable YAML; ``line``/``column`` are 1-based if known."""

    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.line = line
        self.column = column


def _safe() -> YAML:
    yaml = YAML(typ="safe", pure=True)
    yaml.version = (1, 2)
    return yaml


def load(text: str):
    """Plain Python data (dicts, lists, scalars) from YAML 1.2 text."""
    text = text or ""
    if len(text.encode("utf-8")) > MAX_SPEC_BYTES:
        raise SpecYAMLError(f"The spec is larger than {MAX_SPEC_BYTES // 1024} KB.")
    try:
        return _safe().load(text)
    except YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        raise SpecYAMLError(
            str(exc).strip(),
            line=mark.line + 1 if mark else None,
            column=mark.column + 1 if mark else None,
        ) from exc


def dump(data) -> str:
    buf = io.StringIO()
    yaml = YAML(typ="safe", pure=True)
    yaml.default_flow_style = False
    yaml.sort_base_mapping_type_on_output = False
    yaml.dump(data, buf)
    return buf.getvalue()
