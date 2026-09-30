"""The app templates Agent Mode can offer and build on.

A template is a product Zelthy already ships — the PSP template being the first
— where a new client is *described* rather than developed. Templates now live
in the database (``zango.apps.shared.app_templates``): versioned, managed from
the console, and written onto disk for the agents to read. This module keeps
the interface Agent Mode was written against, so its callers don't change.

Nothing here decides whether a template fits. The analyst reads the catalogue
digest and decides; this module only makes the digest.
"""

from __future__ import annotations

from zango.apps.shared.app_templates.services.catalogue import (
    TemplateView as AppTemplate,
)
from zango.apps.shared.app_templates.services.catalogue import (
    catalogue_digest,
    get_template,
    load_templates,
    spec_format_for,
)
from zango.apps.shared.app_templates.services.materialise import templates_root


def templates_dir() -> str:
    """Where templates are materialised for the agents to read (created if missing)."""
    root = templates_root()
    root.mkdir(parents=True, exist_ok=True)
    return str(root)


__all__ = [
    "AppTemplate",
    "catalogue_digest",
    "get_template",
    "load_templates",
    "spec_format_for",
    "templates_dir",
]
