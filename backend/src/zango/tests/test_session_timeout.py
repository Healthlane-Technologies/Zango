"""Unit tests for app/role-level idle-session timeout configuration.

These test the pure resolution + validation logic without a DB / tenant, by
patching ``get_auth_priority`` (the shared auth-precedence merge) and Django
settings. Run with the project test runner, or standalone:

    python -m pytest src/zango/tests/test_session_timeout.py
"""

import os

from unittest import mock

import pytest

# Ensure Django apps are loaded before importing modules that pull in models
# (serializers -> appauth models). Harmless if already configured by a runner.
import django  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_project.settings")
try:
    django.setup()
except Exception:
    pass

from rest_framework import serializers  # noqa: E402


# ---------------------------------------------------------------------------
# get_app_session_timeout: resolution + guard
# ---------------------------------------------------------------------------

PLATFORM = {"SESSION_SECURITY_WARN_AFTER": 1700, "SESSION_SECURITY_EXPIRE_AFTER": 1800}


def _resolve(session_policy):
    """Call get_app_session_timeout with get_auth_priority mocked to return
    the given merged session_policy, and platform defaults fixed."""
    from django.test import override_settings

    from zango.core import utils

    with mock.patch.object(utils, "get_auth_priority", return_value=session_policy):
        with override_settings(**PLATFORM):
            return utils.get_app_session_timeout()


def test_inherits_platform_default_when_unset():
    assert _resolve({}) == (1700, 1800)


def test_inherits_platform_default_when_policy_none():
    assert _resolve(None) == (1700, 1800)


def test_custom_values_used():
    assert _resolve({"session_warn_after": 250, "session_expire_after": 300}) == (250, 300)


def test_partial_override_warn_only_falls_back_expire():
    # Only warn set -> expire inherits platform default (1800); 250 < 1800 is valid.
    assert _resolve({"session_warn_after": 250}) == (250, 1800)


def test_inverted_pair_falls_back_to_platform():
    # warn >= expire is invalid -> platform defaults.
    assert _resolve({"session_warn_after": 500, "session_expire_after": 300}) == (1700, 1800)


def test_non_positive_falls_back_to_platform():
    assert _resolve({"session_warn_after": 0, "session_expire_after": 300}) == (1700, 1800)


# ---------------------------------------------------------------------------
# Serializer validators
# ---------------------------------------------------------------------------

def _validate(auth_config):
    from zango.api.platform.tenancy.v1 import serializers as s

    s.validate_session_policy_timeout(auth_config)


def test_validate_absent_is_ok():
    _validate({})  # no session_policy
    _validate({"session_policy": {}})  # no timeout keys


def test_validate_valid_pair():
    _validate({"session_policy": {"session_warn_after": 250, "session_expire_after": 300}})


@pytest.mark.parametrize(
    "policy",
    [
        {"session_warn_after": -1},
        {"session_warn_after": 0},
        {"session_expire_after": "300"},  # not int
        {"session_expire_after": True},   # bool rejected
        {"session_expire_after": 999999},  # > 24h
        {"session_warn_after": 300, "session_expire_after": 300},  # warn == expire
        {"session_warn_after": 400, "session_expire_after": 300},  # warn > expire
    ],
)
def test_validate_rejects_bad_values(policy):
    with pytest.raises(serializers.ValidationError):
        _validate({"session_policy": policy})


# ---------------------------------------------------------------------------
# Platform hint inject / strip round-trip
# ---------------------------------------------------------------------------

def test_inject_and_strip_platform_hints():
    from zango.api.platform.tenancy.v1 import serializers as s

    with mock.patch.object(s, "get_platform_session_timeout_seconds", return_value=(1700, 1800)):
        with mock.patch.object(s, "get_platform_token_ttl_seconds", return_value=0):
            data = {"auth_config": {"session_policy": {"session_expire_after": 300}}}
            out = s.inject_platform_session_hints(data)
            sp = out["auth_config"]["session_policy"]
            assert sp["platform_session_warn_after"] == 1700
            assert sp["platform_session_expire_after"] == 1800
            assert sp["platform_token_ttl"] == 0
            assert sp["session_expire_after"] == 300  # real value preserved

            # Strip removes only the platform_* hints, leaves real values.
            s.strip_platform_session_hints(out["auth_config"])
            sp2 = out["auth_config"]["session_policy"]
            assert "platform_session_warn_after" not in sp2
            assert "platform_session_expire_after" not in sp2
            assert "platform_token_ttl" not in sp2
            assert sp2["session_expire_after"] == 300
