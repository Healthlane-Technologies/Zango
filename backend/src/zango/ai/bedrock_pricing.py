"""
AWS Bedrock live pricing via the AWS Price List API (``pricing:GetProducts``).

This module is used **only by the off-request pricing refresh task**
(``zango.ai.tasks.refresh_bedrock_pricing``) — never on the LLM request path.
It fetches the public on-demand price list once, parses per-token input/output
rates, and matches them to the bare model IDs in
``BedrockProvider.supported_models``.

Credentials come exclusively from the platform-level Django settings
(``settings.AWS_ACCESS_KEY_ID`` / ``settings.AWS_SECRET_ACCESS_KEY``) — that is
where ``pricing:GetProducts`` access is granted. Provider-config AWS keys are
used to *invoke* Bedrock but are deliberately not used for pricing.

The Price List API endpoint exists only in ``us-east-1`` and ``ap-south-1``,
independent of the Bedrock run region. The run region is used as a *filter*
(via the price list ``location`` attribute), not as the API endpoint.

Every function degrades gracefully: any missing credential, permission error,
or API failure results in an empty result rather than a raised exception, so the
caller (a Celery task) simply writes nothing and known models keep their static
fallback rates.
"""

import json

from loguru import logger

from django.conf import settings


# Pricing API endpoints (the only two regions that host the Price List API).
PRICING_ENDPOINT_REGION = "us-east-1"
PRICING_ENDPOINT_REGION_FALLBACK = "ap-south-1"

# Bedrock run region → human-readable "location" attribute used by the price
# list. Covers every region offered in BedrockProvider.config_fields.aws_region.
REGION_TO_LOCATION = {
    "us-east-1": "US East (N. Virginia)",
    "us-east-2": "US East (Ohio)",
    "us-west-2": "US West (Oregon)",
    "eu-west-1": "Europe (Ireland)",
    "eu-west-3": "Europe (Paris)",
    "eu-central-1": "Europe (Frankfurt)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "ap-south-1": "Asia Pacific (Mumbai)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ca-central-1": "Canada (Central)",
    "sa-east-1": "South America (Sao Paulo)",
}


def _get_settings_credentials():
    """Return (access_key, secret_key) from platform settings, or (None, None).

    Pricing uses the platform-level keys only — that is where
    ``pricing:GetProducts`` is granted.
    """
    access_key = getattr(settings, "AWS_ACCESS_KEY_ID", "") or ""
    secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", "") or ""
    if not access_key or not secret_key:
        return None, None
    return access_key, secret_key


def _build_pricing_client(access_key, secret_key):
    """Build a boto3 ``pricing`` client, trying both endpoint regions."""
    import boto3

    for endpoint_region in (PRICING_ENDPOINT_REGION, PRICING_ENDPOINT_REGION_FALLBACK):
        try:
            return boto3.client(
                "pricing",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=endpoint_region,
            )
        except Exception as e:  # pragma: no cover - region/SDK edge cases
            logger.debug(
                f"[bedrock_pricing] pricing client {endpoint_region} failed: {e}"
            )
    return None


def _normalize(text: str) -> str:
    """Lowercase and strip separators for tolerant token matching."""
    return "".join(c for c in text.lower() if c.isalnum())


def _model_match_tokens(bare_id: str) -> list[str]:
    """Identifying tokens for a bare model ID, used to match a price-list row.

    e.g. ``anthropic.claude-sonnet-4-5-20250929-v1:0`` →
    ``["claudesonnet45", "20250929"]`` — a distinctive family+version token and
    the version date. A row matches only if *all* returned tokens appear in it,
    which keeps matching conservative (no accidental cross-version matches).
    """
    # Drop the vendor prefix ("anthropic.", "amazon.", ...) and the ":0" suffix.
    core = bare_id.split(".", 1)[-1].split(":", 1)[0]
    tokens = []

    # A date-like segment (8 digits) is the strongest disambiguator when present.
    import re

    date_match = re.search(r"\d{8}", core)
    if date_match:
        tokens.append(date_match.group(0))
        # Everything before the date, normalised (e.g. "claude-sonnet-4-5-").
        family = core[: date_match.start()]
    else:
        family = core

    fam_norm = _normalize(family)
    if fam_norm:
        tokens.append(fam_norm)
    return tokens


def _row_matches_model(row_blob: str, tokens: list[str]) -> bool:
    """True if every identifying token appears in the normalised price-list row."""
    if not tokens:
        return False
    return all(tok in row_blob for tok in tokens)


def _parse_price_dimension(dim: dict) -> float | None:
    """Extract a USD price-per-unit from a priceDimension, or None."""
    price_per_unit = (dim.get("pricePerUnit") or {}).get("USD")
    if price_per_unit is None:
        return None
    try:
        return float(price_per_unit)
    except (TypeError, ValueError):
        return None


def _classify_usagetype(usagetype: str, description: str) -> str | None:
    """Classify a price row as 'input' or 'output' tokens, or None if neither.

    Bedrock price rows encode direction in the usagetype (e.g. containing
    "Input-Tokens" / "Output-Tokens") and/or the human description. We check both.
    Cache-token rows are intentionally ignored (out of scope).
    """
    blob = f"{usagetype} {description}".lower()
    if "cache" in blob:
        return None
    if "input" in blob:
        return "input"
    if "output" in blob:
        return "output"
    return None


def fetch_bedrock_rates(regions=None, supported_models=None) -> dict:
    """Fetch live on-demand Bedrock token rates from the AWS Price List API.

    Returns ``{region: {bare_model_id: {"input_per_mtok": float,
    "output_per_mtok": float}}}``. Returns ``{}`` if credentials are missing,
    access is denied, or the API is otherwise unavailable — the caller then
    writes nothing and models keep their static fallback rates.

    Rates are normalised to price-per-million-tokens (AWS lists per-token USD).
    Only regions with an entry in ``REGION_TO_LOCATION`` are queried; by default
    all of them are.
    """
    access_key, secret_key = _get_settings_credentials()
    if not access_key:
        logger.info(
            "[bedrock_pricing] settings.AWS_ACCESS_KEY_ID/SECRET not set — "
            "skipping live pricing (models use static fallback rates)."
        )
        return {}

    if supported_models is None:
        from zango.ai.providers.bedrock import BedrockProvider

        supported_models = BedrockProvider.supported_models

    if regions is None:
        regions = list(REGION_TO_LOCATION.keys())

    try:
        import boto3  # noqa: F401
    except ImportError:
        logger.warning("[bedrock_pricing] boto3 not installed — skipping live pricing.")
        return {}

    client = _build_pricing_client(access_key, secret_key)
    if client is None:
        return {}

    # Pre-compute match tokens once per model.
    model_tokens = {m["id"]: _model_match_tokens(m["id"]) for m in supported_models}

    result: dict = {}
    for region in regions:
        location = REGION_TO_LOCATION.get(region)
        if not location:
            continue
        rates = _fetch_region_rates(client, location, model_tokens)
        if rates:
            result[region] = rates

    return result


def _fetch_region_rates(client, location: str, model_tokens: dict) -> dict:
    """Fetch and parse on-demand rates for a single location.

    Returns ``{bare_model_id: {"input_per_mtok", "output_per_mtok"}}`` for models
    that had at least one recognised price dimension.
    """
    filters = [
        {"Type": "TERM_MATCH", "Field": "ServiceCode", "Value": "AmazonBedrock"},
        {"Type": "TERM_MATCH", "Field": "location", "Value": location},
    ]

    # bare_id -> {"input_per_mtok": x, "output_per_mtok": y}
    region_rates: dict = {}

    try:
        paginator = client.get_paginator("get_products")
        pages = paginator.paginate(
            ServiceCode="AmazonBedrock",
            Filters=filters,
            FormatVersion="aws_v1",
        )
        for page in pages:
            for raw in page.get("PriceList", []):
                _parse_product(raw, model_tokens, region_rates)
    except Exception as e:
        # AccessDenied / throttling / region issue — degrade to no rates.
        logger.warning(f"[bedrock_pricing] get_products failed for {location!r}: {e}")
        return {}

    return region_rates


def _parse_product(raw: str, model_tokens: dict, region_rates: dict) -> None:
    """Parse one PriceList product JSON string, updating ``region_rates`` in place."""
    try:
        product = json.loads(raw)
    except (TypeError, ValueError):
        return

    attrs = product.get("product", {}).get("attributes", {})
    # Only on-demand inference rows carry token pricing; skip everything else fast.
    usagetype = attrs.get("usagetype", "")
    row_blob = _normalize(json.dumps(attrs))

    # Find which supported model (if any) this row prices.
    matched_id = None
    for bare_id, tokens in model_tokens.items():
        if _row_matches_model(row_blob, tokens):
            matched_id = bare_id
            break
    if matched_id is None:
        return

    terms = product.get("terms", {}).get("OnDemand", {})
    for term in terms.values():
        for dim in (term.get("priceDimensions") or {}).values():
            price = _parse_price_dimension(dim)
            if price is None:
                continue
            direction = _classify_usagetype(usagetype, dim.get("description", ""))
            if direction is None:
                continue
            per_mtok = price * 1_000_000
            entry = region_rates.setdefault(matched_id, {})
            key = "input_per_mtok" if direction == "input" else "output_per_mtok"
            # First recognised value wins; on-demand rows shouldn't conflict.
            entry.setdefault(key, round(per_mtok, 6))
