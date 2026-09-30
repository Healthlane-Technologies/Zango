"""Write a template version onto disk, where the agents can read it.

The analyst and the build agent are Claude Code sessions: they load skills from
a plugin directory and read files by path. A version stored in the database is
therefore written out once as a small local plugin::

    <root>/<slug>/<version>-<sha12>/
        .claude-plugin/plugin.json          # plugin "zango-tpl-<slug>"
        skills/<build_skill_name>/...       # the build skill
        requirements/INTERVIEW.md           # what the analyst reads
        requirements/SCHEMA.md
        requirements/schema.json, ui.json, rules.json
        requirements/starter.yaml, example.yaml

The directory name carries the content hash, so a published version maps to
exactly one directory for ever: workers and hosts can each write their own copy
without coordinating, and nothing on disk can go stale. Writes go to a temp
sibling and are renamed into place, so a reader never sees a half-written pack.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid

from pathlib import Path

from django.conf import settings

from .paths import content_sha, normalise_pack_path


REQUIREMENTS_DIR = "requirements"

# Keys a TemplateView.file_path() may be asked for, and the file each maps to.
REQUIREMENT_FILES = {
    "interview": "INTERVIEW.md",
    "schema": "SCHEMA.md",
    "json_schema": "schema.json",
    "ui_schema": "ui.json",
    "rules": "rules.json",
    "starter": "starter.yaml",
    "example": "example.yaml",
}


def templates_root() -> Path:
    override = getattr(settings, "AGENT_MODE_TEMPLATES_DIR", None)
    if override:
        return Path(override)
    return Path(settings.BASE_DIR) / ".agent_mode" / "templates"


def plugin_name(slug: str) -> str:
    return f"zango-tpl-{slug}"


def version_dir(version, sha: str | None = None) -> Path:
    sha = sha or version.content_sha or content_sha(version)
    label = version.version if not version.is_draft else "draft"
    return templates_root() / version.template.slug / f"{label}-{sha[:12]}"


def _requirement_documents(version) -> dict:
    """The analyst-facing files, keyed by file name. Empty ones are omitted."""
    docs = {
        "INTERVIEW.md": version.interview_md,
        "SCHEMA.md": version.schema_md,
        "starter.yaml": version.starter_yaml,
        "example.yaml": version.example_yaml,
    }
    if version.json_schema:
        docs["schema.json"] = json.dumps(version.json_schema, indent=2)
    if version.ui_schema:
        docs["ui.json"] = json.dumps(version.ui_schema, indent=2)
    if version.rules:
        docs["rules.json"] = json.dumps(version.rules, indent=2)
    return {name: text for name, text in docs.items() if text}


def _write(root: Path, rel: str, text: str) -> None:
    target = (root / rel).resolve()
    if not str(target).startswith(str(root.resolve()) + os.sep):
        raise ValueError(f"refusing to write outside the pack: {rel}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def materialise(version) -> Path:
    """The on-disk directory for ``version``, writing it first if needed."""
    sha = version.content_sha or content_sha(version)
    dest = version_dir(version, sha)
    if dest.is_dir():
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.parent / f".tmp-{uuid.uuid4().hex}"
    try:
        template = version.template
        manifest = {
            "name": plugin_name(template.slug),
            "description": f"{template.name} template v{version.version}: "
            "the build skill and requirement documents.",
            "version": version.version,
            "author": {"name": "Zango"},
        }
        _write(tmp, ".claude-plugin/plugin.json", json.dumps(manifest, indent=2))

        for name, text in _requirement_documents(version).items():
            _write(tmp, f"{REQUIREMENTS_DIR}/{name}", text)

        skill = version.build_skill_name
        if skill:
            for row in version.files.all():
                rel = normalise_pack_path(row.path)
                _write(tmp, f"skills/{skill}/{rel}", row.content)

        try:
            os.rename(tmp, dest)
        except OSError:
            # Someone else finished first; theirs is identical by construction.
            if not dest.is_dir():
                raise
    finally:
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
    return dest
