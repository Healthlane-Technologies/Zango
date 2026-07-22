"""
Unit tests for app/role-level idle-session timeout configuration.

These test the pure resolution + validation logic without a DB / tenant, by
patching ``get_auth_priority`` (the shared auth-precedence merge) and Django
settings.

Three sub-groups:
  a) get_app_session_timeout — resolution + guard (get_auth_priority mocked)
  b) all.html rendering       — template loader + rendered timer values
  c) serializer validators    — validate_session_policy_timeout, hint round-trip
"""

from unittest import mock

from django.db import connection
from django.test import SimpleTestCase, override_settings

from rest_framework import serializers

from zango.core import utils


PLATFORM = {"SESSION_SECURITY_WARN_AFTER": 1700, "SESSION_SECURITY_EXPIRE_AFTER": 1800}


def _resolve(session_policy):
    """Call get_app_session_timeout with get_auth_priority mocked to return
    the given merged session_policy, and platform defaults fixed."""
    # Pretend we're on a tenant schema; the public schema short-circuits to the
    # platform defaults (see PublicSchemaTest).
    with mock.patch.object(connection, "schema_name", "sometenant"):
        with mock.patch.object(utils, "get_auth_priority", return_value=session_policy):
            with override_settings(**PLATFORM):
                return utils.get_app_session_timeout()


# ─── a) get_app_session_timeout: resolution + guard ───────────────────────────

class GetAppSessionTimeoutTest(SimpleTestCase):

    def test_inherits_platform_default_when_unset(self):
        self.assertEqual(_resolve({}), (1700, 1800))

    def test_inherits_platform_default_when_policy_none(self):
        self.assertEqual(_resolve(None), (1700, 1800))

    def test_custom_values_used(self):
        self.assertEqual(
            _resolve({"session_warn_after": 250, "session_expire_after": 300}),
            (250, 300),
        )

    def test_partial_override_warn_only_falls_back_expire(self):
        # Only warn set -> expire inherits platform default (1800); 250 < 1800 is valid.
        self.assertEqual(_resolve({"session_warn_after": 250}), (250, 1800))

    def test_inverted_pair_falls_back_to_platform(self):
        # Both explicitly set but inverted -> platform defaults.
        self.assertEqual(
            _resolve({"session_warn_after": 500, "session_expire_after": 300}),
            (1700, 1800),
        )

    def test_non_positive_key_is_treated_as_inherit(self):
        """A non-positive (invalid) warn must not discard an explicit, valid logout;
        it's treated as "inherit", and the warning is derived inside the window."""
        self.assertEqual(
            _resolve({"session_warn_after": 0, "session_expire_after": 300}), (240, 300)
        )
        self.assertEqual(
            _resolve({"session_warn_after": -5, "session_expire_after": 3600}),
            (1700, 3600),
        )

    def test_short_logout_with_inherited_warning_keeps_configured_logout(self):
        """Warn and logout are configured independently, so an admin can set a short
        logout while the warning still inherits the (much longer) platform default.
        The explicit logout must win -- deriving a warning inside it rather than
        discarding both values."""
        # expire=300 (5 min) but platform warn is 1700 (28 min), which doesn't fit.
        self.assertEqual(_resolve({"session_expire_after": 300}), (240, 300))

    def test_short_logout_derives_at_least_half_the_window(self):
        # 60s logout: expire - 60 would be 0, so fall back to half the window.
        self.assertEqual(_resolve({"session_expire_after": 60}), (30, 60))

    def test_long_logout_keeps_inherited_warning(self):
        # Platform warn (1700) fits inside a 3600s logout, so it is kept as-is.
        self.assertEqual(_resolve({"session_expire_after": 3600}), (1700, 3600))


class PublicSchemaTest(SimpleTestCase):

    def test_public_schema_returns_platform_default_without_resolving(self):
        """The platform app panel (public schema) has no tenant auth_config, and
        get_auth_priority queries tenant-only tables (SAMLModel) that don't exist
        there. Regression: it must not be called at all. See app_panel.html, which
        includes session_security/all.html."""
        with mock.patch.object(connection, "schema_name", "public"):
            with mock.patch.object(
                utils, "get_auth_priority", side_effect=AssertionError("must not resolve")
            ) as spy:
                with override_settings(**PLATFORM):
                    self.assertEqual(utils.get_app_session_timeout(), (1700, 1800))
                spy.assert_not_called()

    def test_resolution_error_falls_back_to_platform(self):
        """A failure resolving auth config must never 500 the page render."""
        with mock.patch.object(connection, "schema_name", "sometenant"):
            with mock.patch.object(
                utils, "get_auth_priority", side_effect=Exception("db boom")
            ):
                with override_settings(**PLATFORM):
                    self.assertEqual(utils.get_app_session_timeout(), (1700, 1800))


# ─── b) all.html rendering ────────────────────────────────────────────────────

def _render_all_html():
    """Render our all.html for an authenticated user and pull the JS timer values."""
    import re

    from django.template.loader import render_to_string

    class _User:
        is_authenticated = True

    class _Request:
        user = _User()

    html = render_to_string("session_security/all.html", {"request": _Request()})
    match = re.search(r"warnAfter: (\d+),\s*expireAfter: (\d+)", html)
    assert match, f"timer config not found in rendered template:\n{html}"
    return tuple(int(g) for g in match.groups())


class AllHtmlTest(SimpleTestCase):

    def test_zango_all_html_wins_over_library_template(self):
        """Legacy apps do {% include 'session_security/all.html' %}. Ours must be the
        one that resolves (via the filesystem loader), not django-session-security's,
        otherwise the client silently falls back to the platform-global numbers."""
        from django.template.loader import get_template

        origin = get_template("session_security/all.html").origin.name
        self.assertIn(
            "zango/templates/session_security/all.html",
            origin.replace("\\", "/"),
            origin,
        )

    def test_all_html_renders_per_app_role_values(self):
        with mock.patch.object(connection, "schema_name", "sometenant"):
            with mock.patch.object(
                utils,
                "get_auth_priority",
                return_value={"session_warn_after": 250, "session_expire_after": 300},
            ):
                self.assertEqual(_render_all_html(), (250, 300))

    def test_all_html_on_public_schema_uses_platform_default(self):
        """The app panel (public schema) renders without touching tenant tables."""
        with mock.patch.object(connection, "schema_name", "public"):
            with mock.patch.object(
                utils, "get_auth_priority", side_effect=AssertionError("must not resolve")
            ):
                with override_settings(**PLATFORM):
                    self.assertEqual(_render_all_html(), (1700, 1800))


# ─── c) Serializer validators ─────────────────────────────────────────────────

def _validate(auth_config):
    from zango.api.platform.tenancy.v1 import serializers as s

    s.validate_session_policy_timeout(auth_config)


class ValidateSessionPolicyTimeoutTest(SimpleTestCase):

    def test_validate_absent_is_ok(self):
        _validate({})  # no session_policy
        _validate({"session_policy": {}})  # no timeout keys

    def test_validate_valid_pair(self):
        _validate(
            {"session_policy": {"session_warn_after": 250, "session_expire_after": 300}}
        )

    def test_validate_rejects_bad_values(self):
        bad_policies = [
            {"session_warn_after": -1},
            {"session_warn_after": 0},
            {"session_expire_after": "300"},  # not int
            {"session_expire_after": True},   # bool rejected
            {"session_expire_after": 999999},  # > 24h
            {"session_warn_after": 300, "session_expire_after": 300},  # warn == expire
            {"session_warn_after": 400, "session_expire_after": 300},  # warn > expire
        ]
        for policy in bad_policies:
            with self.subTest(policy=policy):
                with self.assertRaises(serializers.ValidationError):
                    _validate({"session_policy": policy})


class PlatformHintRoundTripTest(SimpleTestCase):

    def test_inject_and_strip_platform_hints(self):
        from zango.api.platform.tenancy.v1 import serializers as s

        with mock.patch.object(
            s, "get_platform_session_timeout_seconds", return_value=(1700, 1800)
        ):
            with mock.patch.object(
                s, "get_platform_token_ttl_seconds", return_value=0
            ):
                data = {"auth_config": {"session_policy": {"session_expire_after": 300}}}
                out = s.inject_platform_session_hints(data)
                sp = out["auth_config"]["session_policy"]
                self.assertEqual(sp["platform_session_warn_after"], 1700)
                self.assertEqual(sp["platform_session_expire_after"], 1800)
                self.assertEqual(sp["platform_token_ttl"], 0)
                self.assertEqual(sp["session_expire_after"], 300)  # real value preserved

                # Strip removes only the platform_* hints, leaves real values.
                s.strip_platform_session_hints(out["auth_config"])
                sp2 = out["auth_config"]["session_policy"]
                self.assertNotIn("platform_session_warn_after", sp2)
                self.assertNotIn("platform_session_expire_after", sp2)
                self.assertNotIn("platform_token_ttl", sp2)
                self.assertEqual(sp2["session_expire_after"], 300)
