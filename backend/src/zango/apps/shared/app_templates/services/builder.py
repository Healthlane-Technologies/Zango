"""A template's custom requirement builder, served as one page.

The builder page is stored as-is; the adapter (a small script speaking the
platform's postMessage protocol) is injected just before its last ``</body>``,
so it runs after the page's own scripts and can drive them.
"""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError


MAX_BUILDER_BYTES = 8 * 1024 * 1024
_LAST_BODY = re.compile(r"</body>(?![\s\S]*</body>)", re.IGNORECASE)


def compose(version) -> str:
    """The builder page with the adapter injected."""
    if not version.has_builder:
        raise ValidationError(f"{version} has no custom builder.")
    script = (
        "<script>\n"
        + version.builder_adapter.replace("</script", "<\\/script")
        + "\n</script>\n"
    )
    html = version.builder_html
    if _LAST_BODY.search(html):
        return _LAST_BODY.sub(lambda m: script + m.group(0), html, count=1)
    return html + script


def attach_builder(version, html: str, adapter: str | None = None) -> None:
    """Put a builder page (and optionally a new adapter) on a draft version."""
    from ..models import ImmutableVersionError

    if not version.is_draft:
        raise ImmutableVersionError(
            f"{version} is {version.status}; attach the builder to a new draft."
        )
    html = html or ""
    if not html.strip():
        raise ValidationError("The builder page is empty.")
    if len(html.encode("utf-8")) > MAX_BUILDER_BYTES:
        raise ValidationError(
            f"The builder page is larger than {MAX_BUILDER_BYTES // (1024 * 1024)} MB."
        )
    version.builder_html = html
    if adapter is not None:
        version.builder_adapter = adapter
    version.save()
