"""Import the packs that ship with Zango into the catalogue after migrate.

Deploying Zango runs migrations; hooking the bundled packs onto post_migrate
means a fresh install, an upgrade and a test database all get the shipped
templates without a separate step. Imports are idempotent (keyed by content
hash), so running this on every migrate is cheap and never duplicates.
"""

from __future__ import annotations

import logging

from pathlib import Path

from django.conf import settings
from django.db import connection


logger = logging.getLogger("zango.app_templates")

PACKS_DIR = Path(__file__).parent / "packs"


def bundled_packs() -> list[Path]:
    if not PACKS_DIR.is_dir():
        return []
    import json

    from .services.generic import GENERIC_SLUG

    def generic_first(pack: Path):
        # Lean packs borrow from the generic one: it must be published first.
        try:
            slug = json.loads((pack / "template.json").read_text()).get("slug")
        except ValueError:
            slug = None
        return (slug != GENERIC_SLUG, pack.name)

    return sorted(
        (p for p in PACKS_DIR.iterdir() if (p / "template.json").is_file()),
        key=generic_first,
    )


def seed_bundled_packs(sender=None, **kwargs):
    if not getattr(settings, "ZANGO_SEED_APP_TEMPLATES", True):
        return
    # django-tenants runs post_migrate once per schema; the catalogue is public.
    if getattr(connection, "schema_name", "public") != "public":
        return
    from .services.packs import import_pack

    for pack in bundled_packs():
        try:
            version, created = import_pack(pack, publish_now=True, by="zango")
            if created:
                logger.info("app_templates: imported %s %s", pack.name, version.version)
        except Exception:
            # A broken bundled pack must not break migrate; it is simply not offered.
            logger.exception(
                "app_templates: could not import bundled pack %s", pack.name
            )
