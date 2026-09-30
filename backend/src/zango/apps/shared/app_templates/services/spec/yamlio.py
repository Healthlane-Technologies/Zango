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


# --- round trip -------------------------------------------------------------
# The agent and the user edit the same draft, and the starter carries guidance
# comments for both. Edits therefore go through ruamel's round-trip mode, which
# keeps comments and key order; ``to_plain`` gives validators ordinary data.


def _rt() -> YAML:
    yaml = YAML(typ="rt")
    yaml.version = (1, 2)
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096
    return yaml


def load_rt(text: str):
    """A comment-preserving document (CommentedMap/Seq) from YAML 1.2 text."""
    text = text or ""
    if len(text.encode("utf-8")) > MAX_SPEC_BYTES:
        raise SpecYAMLError(f"The spec is larger than {MAX_SPEC_BYTES // 1024} KB.")
    try:
        return _rt().load(text)
    except YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        raise SpecYAMLError(
            str(exc).strip(),
            line=mark.line + 1 if mark else None,
            column=mark.column + 1 if mark else None,
        ) from exc


def dump_rt(doc) -> str:
    buf = io.StringIO()
    rt = _rt()
    rt.version = None  # don't write a %YAML directive into the spec
    rt.dump(doc, buf)
    return buf.getvalue()


def to_plain(node):
    """Ordinary dicts/lists/scalars from a round-trip document.

    ruamel's ScalarBoolean is an int, not a bool, so JSON Schema would reject
    every ``true`` in the spec if validators saw the round-trip types.
    """
    from ruamel.yaml.scalarbool import ScalarBoolean
    from ruamel.yaml.scalarfloat import ScalarFloat

    if isinstance(node, dict):
        return {
            str(k) if not isinstance(k, (int, float, bool)) else k: to_plain(v)
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [to_plain(v) for v in node]
    if isinstance(node, (bool, ScalarBoolean)):
        return bool(node)
    if isinstance(node, ScalarFloat):
        return float(node)
    if isinstance(node, int):
        return int(node)
    if isinstance(node, str):
        return str(node)
    return node
