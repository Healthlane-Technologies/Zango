"""The catalogue of app templates the analyst may offer.

A template is a product Zelthy already ships — the PSP template being the first
— where a new client is *described* rather than developed. When a user's opening
ask is plainly one of those, the most valuable thing the analyst can do is say
so, because the alternative is rebuilding software that already exists.

The packs live inside the analyst skill (``skill_plugin/skills/
zango-requirements-analyst/templates/<slug>/``) rather than next to this module,
and that is deliberate: the analyst has to *read* them, and the skill plugin
directory is the one tree it can already reach. One copy on disk, two readers.

Nothing here decides whether a template fits. A keyword table would offer the
PSP template to anyone who said "patient", and refuse it to someone describing
a co-pay assistance program without ever using the word. The model reads the
catalogue digest and decides; this module only makes the digest, and validates
that each pack is complete enough to be worth offering.
"""

from __future__ import annotations

import json
import logging
import os

from dataclasses import dataclass, field
from functools import lru_cache


logger = logging.getLogger("zango.agent_mode")

MANIFEST = "template.json"

# Files a pack must actually have on disk. A manifest that names an interview
# the analyst cannot open produces a conversation that stalls halfway with the
# user already committed, which is worse than never offering it.
REQUIRED_FILES = ("interview", "schema")

SPEC_FORMATS = ("markdown", "yaml")

MAX_SLUG = 64


def templates_dir() -> str:
    from .options import SKILL_PLUGIN_DIR

    return os.path.join(
        SKILL_PLUGIN_DIR, "skills", "zango-requirements-analyst", "templates"
    )


@dataclass(frozen=True)
class AppTemplate:
    slug: str
    name: str
    one_liner: str
    path: str
    spec_format: str = "markdown"
    spec_root: str = ""
    aka: tuple = ()
    fits_when: tuple = ()
    gives_you: tuple = ()
    sections: tuple = ()
    files: dict = field(default_factory=dict)

    @property
    def is_yaml(self) -> bool:
        return self.spec_format == "yaml"

    def file_path(self, key: str) -> str:
        """Absolute path of one of the pack's documents, or "" if it has none."""
        name = self.files.get(key)
        return os.path.join(self.path, name) if name else ""


def _tuple_of_strings(value, limit: int = 12) -> tuple:
    if not isinstance(value, list):
        return ()
    out = []
    for item in value[:limit]:
        text = str(item).strip()
        if text:
            out.append(text)
    return tuple(out)


def _load_one(slug: str, path: str):
    """One template from its directory, or None if the pack is unusable."""
    manifest_path = os.path.join(path, MANIFEST)
    try:
        with open(manifest_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        logger.exception("agent_mode: template %s has an unreadable manifest", slug)
        return None
    if not isinstance(data, dict):
        return None

    # The directory name is the slug. A manifest that disagrees would make the
    # `zango-template` fence unresolvable, so the directory wins.
    name = str(data.get("name") or "").strip()
    one_liner = str(data.get("one_liner") or "").strip()
    if not name or not one_liner:
        logger.warning("agent_mode: template %s is missing name/one_liner", slug)
        return None

    spec_format = str(data.get("spec_format") or "markdown").strip().lower()
    if spec_format not in SPEC_FORMATS:
        spec_format = "markdown"

    files = {}
    for key in ("interview", "schema", "starter", "example"):
        filename = str(data.get(key) or "").strip()
        if filename and os.path.isfile(os.path.join(path, filename)):
            files[key] = filename

    missing = [key for key in REQUIRED_FILES if key not in files]
    if missing:
        logger.warning(
            "agent_mode: template %s is incomplete, not offering it (missing %s)",
            slug,
            ", ".join(missing),
        )
        return None

    sections = tuple(
        (str(s.get("id") or "").strip(), str(s.get("title") or "").strip())
        for s in (data.get("sections") or [])
        if isinstance(s, dict) and s.get("id")
    )

    return AppTemplate(
        slug=slug,
        name=name,
        one_liner=one_liner,
        path=path,
        spec_format=spec_format,
        spec_root=str(data.get("spec_root") or "").strip(),
        aka=_tuple_of_strings(data.get("aka"), 8),
        fits_when=_tuple_of_strings(data.get("fits_when")),
        gives_you=_tuple_of_strings(data.get("gives_you")),
        sections=sections,
        files=files,
    )


@lru_cache(maxsize=1)
def load_templates() -> dict:
    """Every usable template, keyed by slug. Cached — packs ship with the code."""
    root = templates_dir()
    found = {}
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return found
    for entry in entries:
        path = os.path.join(root, entry)
        if not os.path.isdir(path) or entry.startswith((".", "_")):
            continue
        template = _load_one(entry[:MAX_SLUG], path)
        if template is not None:
            found[template.slug] = template
    return found


def get_template(slug: str):
    """One template by slug, or None. Safe to call with user/model input."""
    if not slug:
        return None
    return load_templates().get(str(slug).strip().lower()[:MAX_SLUG])


def catalogue_digest() -> str:
    """What the analyst is told about the templates, on its first turn.

    Enough to decide whether to offer one and to describe it convincingly,
    and nothing more: the pack itself is only opened once the user says yes,
    so a declined offer costs a few hundred tokens rather than a file read.
    """
    templates = load_templates()
    if not templates:
        return ""

    blocks = []
    for template in templates.values():
        lines = [f"### {template.name}  (slug: {template.slug})"]
        if template.aka:
            lines.append(f"also called: {', '.join(template.aka)}")
        lines.append(template.one_liner)
        if template.fits_when:
            lines.append("Offer it when:")
            lines.extend(f"  - {item}" for item in template.fits_when)
        if template.gives_you:
            lines.append("Already built:")
            lines.extend(f"  - {item}" for item in template.gives_you)
        lines.append(f"pack: {template.path}/")
        lines.append(
            f"spec format: {template.spec_format}"
            + (f" (root key `{template.spec_root}`)" if template.spec_root else "")
        )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def spec_format_for(slug: str) -> str:
    """The spec format a requirement on this template should be stored as."""
    template = get_template(slug)
    return template.spec_format if template else "markdown"
