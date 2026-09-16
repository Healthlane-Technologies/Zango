"""Automatic subdomain allocation for newly launched apps.

Names are two random words — readable, and unrelated to the app's own name so
nothing about the app leaks through its URL. ``Domain.domain`` is unique, so
allocation is a claim-and-retry loop rather than a check-then-write: two apps
launched at the same instant would otherwise pass the same existence check.
"""

from __future__ import annotations

import logging
import re
import secrets


log = logging.getLogger(__name__)

ADJECTIVES = (
    "amber azure bold brave bright brisk calm clever coral crimson curious "
    "daring deft eager early fair fleet fond gentle giant glad golden grand "
    "happy hardy hidden humble ivory jolly keen kind lively lucid lunar merry "
    "mellow mighty mint misty noble nimble olive prime proud quick quiet rapid "
    "regal ruby rustic sage scarlet serene sharp silent silver smooth solar "
    "spry stellar sturdy sunny swift teal tidy timber tranquil trusty upbeat "
    "urban vivid warm whole wise witty zesty"
).split()

NOUNS = (
    "acorn alder anchor arbor arrow aspen badger basin beacon birch bison "
    "bloom bluff branch breeze brook canyon cedar cliff cove crane creek "
    "delta dune eagle ember falcon fern field finch fjord forest garnet "
    "glade grove harbor haven heron hill isle juniper kestrel lagoon lantern "
    "ledge maple meadow mesa moss oak orchard osprey otter pebble pine plume "
    "pond quarry rapids reef ridge river shore slate sparrow spring summit "
    "thicket tide trail valley vista willow"
).split()

# A conservative hostname label: lowercase, digits, inner hyphens, <= 63 chars.
_LABEL = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
# The base domain itself: one or more dot-separated labels.
_BASE_DOMAIN = re.compile(
    r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$"
)

MAX_ATTEMPTS = 12
# Past this many collisions, widen the space instead of retrying the same one.
WIDEN_AFTER = 6


def normalise_base_domain(value: str) -> str:
    """Trim the things people paste in — scheme, trailing slash, leading dot."""
    text = (value or "").strip().lower()
    text = re.sub(r"^[a-z]+://", "", text)
    text = text.split("/", 1)[0]
    text = text.strip().strip(".")
    return text


def is_valid_base_domain(value: str) -> bool:
    domain = normalise_base_domain(value)
    return bool(domain) and len(domain) <= 253 and bool(_BASE_DOMAIN.match(domain))


def random_label(widen: bool = False) -> str:
    label = f"{secrets.choice(ADJECTIVES)}-{secrets.choice(NOUNS)}"
    if widen:
        label = f"{label}-{secrets.token_hex(2)}"
    return label


def candidate_domains(base_domain: str, attempts: int = MAX_ATTEMPTS):
    """Yield candidate hostnames, widening the namespace after repeat clashes."""
    base = normalise_base_domain(base_domain)
    for i in range(attempts):
        label = random_label(widen=i >= WIDEN_AFTER)
        if _LABEL.match(label):
            yield f"{label}.{base}"


def allocate_domain(tenant, settings_row=None):
    """Attach an auto-allocated domain to ``tenant``.

    Returns the created ``Domain``, or None when allocation is off, the base
    domain is unusable, or every candidate collided. Never raises: an app that
    launches without a domain is recoverable, a launch that crashes is not.
    """
    from django.db import IntegrityError, transaction

    from ..tenancy.models import Domain

    try:
        if settings_row is None:
            from .models import PlatformSettings

            settings_row = PlatformSettings.load()

        if not settings_row.auto_domain_enabled:
            return None
        if not is_valid_base_domain(settings_row.base_domain):
            log.warning(
                "platform_settings: auto domain is on but base_domain %r is not "
                "a valid domain — skipping allocation for %s",
                settings_row.base_domain,
                getattr(tenant, "name", "?"),
            )
            return None

        # Never take a second domain for an app that already has one.
        if Domain.objects.filter(tenant=tenant).exists():
            return None

        is_primary = bool(settings_row.auto_domain_is_primary)
        for domain in candidate_domains(settings_row.base_domain):
            try:
                with transaction.atomic():
                    return Domain.objects.create(
                        domain=domain, tenant=tenant, is_primary=is_primary
                    )
            except IntegrityError:
                # Taken between generating it and claiming it. Try another.
                continue

        log.warning(
            "platform_settings: could not allocate a subdomain under %r for %s "
            "after %s attempts",
            settings_row.base_domain,
            getattr(tenant, "name", "?"),
            MAX_ATTEMPTS,
        )
        return None
    except Exception:  # noqa: BLE001 - allocation must never break a launch
        log.exception("platform_settings: domain allocation failed")
        return None
