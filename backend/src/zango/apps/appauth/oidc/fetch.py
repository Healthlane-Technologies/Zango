"""Outbound HTTP for OIDC configuration screens (discovery, test connection).

The issuer URL is typed by an App Panel user, so requests are limited to
https (http only when DEBUG), public addresses, no redirects, a short timeout
and a size cap.
"""

import ipaddress
import socket

from urllib.parse import urlparse

import requests

from django.conf import settings


TIMEOUT_SECONDS = 5
MAX_BYTES = 512 * 1024
WELL_KNOWN = "/.well-known/openid-configuration"


class FetchError(Exception):
    pass


def discovery_url(issuer):
    return issuer.rstrip("/") + WELL_KNOWN


def _check_url(url):
    parsed = urlparse(url)
    allowed = {"https", "http"} if settings.DEBUG else {"https"}
    if parsed.scheme not in allowed or not parsed.hostname:
        raise FetchError("Only https URLs are allowed.")
    if settings.DEBUG:
        return
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    except socket.gaierror as e:
        raise FetchError(f"Could not resolve {parsed.hostname}.") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise FetchError(f"{parsed.hostname} resolves to a non-public address.")


def _read(resp):
    body = b""
    for chunk in resp.iter_content(8192):
        body += chunk
        if len(body) > MAX_BYTES:
            raise FetchError("Response is too large.")
    return body


def safe_request(method, url, **kwargs):
    _check_url(url)
    try:
        resp = requests.request(
            method,
            url,
            timeout=TIMEOUT_SECONDS,
            allow_redirects=False,
            stream=True,
            **kwargs,
        )
        body = _read(resp)
    except requests.RequestException as e:
        raise FetchError(f"Request to {url} failed: {e.__class__.__name__}.") from e
    return resp, body


def fetch_json(url):
    resp, body = safe_request("GET", url)
    if resp.status_code != 200:
        raise FetchError(f"GET {url} returned {resp.status_code}.")
    try:
        import json

        return json.loads(body)
    except ValueError as e:
        raise FetchError(f"GET {url} did not return JSON.") from e


REQUIRED_DISCOVERY_KEYS = (
    "issuer",
    "authorization_endpoint",
    "token_endpoint",
    "jwks_uri",
)


def fetch_discovery(issuer):
    """Returns the discovery document, checking that its issuer matches exactly."""
    config = fetch_json(discovery_url(issuer))
    if not isinstance(config, dict):
        raise FetchError("Discovery document is not a JSON object.")
    missing = [k for k in REQUIRED_DISCOVERY_KEYS if not config.get(k)]
    if missing:
        raise FetchError(f"Discovery document is missing: {', '.join(missing)}.")
    if config["issuer"] != issuer:
        raise FetchError(
            f"Discovery issuer '{config['issuer']}' does not match '{issuer}'."
        )
    return config
