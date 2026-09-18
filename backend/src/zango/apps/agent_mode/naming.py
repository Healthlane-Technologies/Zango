"""Choose an app identity from a one-line ask.

"Build with Agent" starts before the app exists, so something has to invent
the name the tenant, schema and workspace directory will all carry forever.
The model does it — it reads the ask the way a person would — but the result
is put through the same validation a hand-typed name faces, because a schema
name is not a place to trust free text: ``SQL_IDENTIFIER_RE`` allows only
``[_a-zA-Z][_a-zA-Z0-9]{4,30}``, and the column caps it at 30.

A model call is never on the critical path for correctness: every failure
mode — no key, no ``anthropic`` package, a refusal, malformed JSON, a name
that survives none of the cleaning — falls back to a slug derived from the
ask itself, so an app always gets created.
"""

from __future__ import annotations

import json
import re

from dataclasses import dataclass


# Kept in step with zango.apps.shared.tenancy.models.SQL_IDENTIFIER_RE.
MIN_NAME_LEN = 5
MAX_NAME_LEN = 30

# Words that say nothing about the app, so they never earn a place in a name
# that is capped at 30 characters.
_STOPWORDS = {
    "a", "an", "and", "app", "application", "are", "as", "at", "be", "build",
    "can", "create", "for", "from", "have", "i", "in", "into", "is", "it",
    "like", "make", "me", "my", "need", "of", "on", "or", "our", "should",
    "simple", "so", "system", "that", "the", "their", "them", "then", "there",
    "they", "this", "to", "track", "want", "was", "we", "where", "which",
    "who", "will", "with", "would", "you", "your",
}

# Schema names Postgres or Zango already own.
RESERVED_NAMES = {"public", "template", "postgres", "zango", "platform", "shared"}

_NAME_PROMPT = """\
Name a new business application from this one-line description.

Description: {prompt}

Reply with ONLY a JSON object, no prose and no code fence:

{{"name": "<identifier>", "label": "<Title Case Name>", "description": "<one sentence>"}}

Rules for "name":
- lowercase letters, digits and underscores only
- starts with a letter
- between {min_len} and {max_len} characters
- names what the app is for, not what it is built with (e.g. "clinic_visits",
  "loan_approvals", "field_service_jobs")
- no version numbers, no "app"/"system"/"portal" filler unless it is the
  clearest word available

"label" is the same name written for people, at most 60 characters.
"description" is one plain sentence a non-technical user would recognise.
"""


@dataclass(frozen=True)
class AppIdentity:
    name: str
    label: str
    description: str
    # "model" | "fallback" — surfaced in the API so a silent downgrade to the
    # slug path is visible rather than mysterious.
    source: str


def sanitize_name(raw: str) -> str:
    """Coerce a proposed name into a legal tenant name, or return ""."""
    text = (raw or "").strip().lower()
    # camelCase and spaced words both become underscore-separated.
    text = re.sub(r"[\s\-./]+", "_", text)
    text = re.sub(r"[^a-z0-9_]", "", text)
    text = re.sub(r"_{2,}", "_", text).strip("_")
    # Must start with a letter: a leading digit is not a legal identifier.
    text = re.sub(r"^[0-9_]+", "", text)
    if not text:
        return ""
    text = text[:MAX_NAME_LEN].rstrip("_")
    if len(text) < MIN_NAME_LEN or text in RESERVED_NAMES:
        return ""
    return text


def slug_from_prompt(prompt: str) -> str:
    """Deterministic fallback name built from the ask's own words."""
    words = [
        word
        for word in re.findall(r"[a-zA-Z][a-zA-Z0-9]*", (prompt or "").lower())
        if word not in _STOPWORDS and len(word) > 2
    ]
    candidate = ""
    for word in words[:3]:
        nxt = f"{candidate}_{word}" if candidate else word
        if len(nxt) > MAX_NAME_LEN:
            break
        candidate = nxt
    name = sanitize_name(candidate)
    return name or "new_app"


def label_from_name(name: str) -> str:
    return " ".join(part.capitalize() for part in (name or "").split("_") if part)


def unique_name(base: str) -> str:
    """First free variant of ``base``.

    Suffixes are appended inside the 30-character budget rather than beyond
    it, so the result is always a legal tenant name.
    """
    from zango.apps.shared.tenancy.models import TenantModel

    base = sanitize_name(base) or "new_app"
    # One query for the whole stem: the suffix loop below must not issue 98
    # round trips to find a free variant.
    taken = set(
        TenantModel.objects.filter(name__startswith=base[: MAX_NAME_LEN - 3]).values_list(
            "name", flat=True
        )
    )
    if base not in taken and base not in RESERVED_NAMES:
        return base

    for index in range(2, 100):
        suffix = f"_{index}"
        stem = base[: MAX_NAME_LEN - len(suffix)].rstrip("_")
        # Trimming can drop the stem under the minimum length; pad rather
        # than emit something the tenant-name check would reject.
        while len(stem) + len(suffix) < MIN_NAME_LEN:
            stem += "x"
        candidate = f"{stem}{suffix}"
        if candidate not in taken:
            return candidate

    # 98 collisions on one stem is not a real scenario, but a name must still
    # come back rather than an exception.
    from uuid import uuid4

    stem = base[: MAX_NAME_LEN - 7].rstrip("_")
    return f"{stem}_{uuid4().hex[:6]}"


def _parse(text: str) -> dict:
    """Pull the JSON object out of a reply, fence or prose notwithstanding."""
    if not text:
        return {}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def suggest_identity(prompt: str, creds=None, *, timeout: float = 30.0) -> AppIdentity:
    """Ask the model to name the app; fall back to a slug if it cannot.

    Uses the Messages API rather than the Agent SDK: naming needs no tools,
    no workspace and no session, and starting the Claude Code CLI for one
    short completion would add seconds to the only step the user is watching.
    """
    from .config import load_config
    from .credentials import resolve_credentials

    prompt = (prompt or "").strip()
    fallback_name = slug_from_prompt(prompt)
    fallback = AppIdentity(
        name=fallback_name,
        label=label_from_name(fallback_name),
        description=prompt[:500],
        source="fallback",
    )

    creds = creds or resolve_credentials()
    if not creds.is_usable or not prompt:
        return fallback

    cfg = load_config()
    model = cfg.analyst_model or cfg.model or "claude-opus-5"
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=creds.api_key, timeout=timeout)
        reply = client.messages.create(
            model=model,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": _NAME_PROMPT.format(
                        prompt=prompt[:2000],
                        min_len=MIN_NAME_LEN,
                        max_len=MAX_NAME_LEN,
                    ),
                }
            ],
        )
        text = "".join(
            getattr(block, "text", "") or "" for block in (reply.content or [])
        )
    except Exception:  # noqa: BLE001 - naming must never block a launch
        import logging

        logging.getLogger("zango.agent_mode").exception(
            "agent_mode: could not name the app; falling back to a slug"
        )
        return fallback

    data = _parse(text)
    name = sanitize_name(str(data.get("name") or ""))
    if not name:
        return fallback

    label = str(data.get("label") or "").strip()[:120] or label_from_name(name)
    description = str(data.get("description") or "").strip()[:2000] or prompt[:500]
    return AppIdentity(
        name=name, label=label, description=description, source="model"
    )
