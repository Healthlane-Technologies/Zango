"""Resolved Agent Mode configuration.

The settings UI and the runners must agree: a value saved in the App Panel
has to reach ClaudeAgentOptions, and a value the operator never set has to
fall back rather than becoming empty.
"""

import unittest

from zango.apps.agent_mode.config import AgentModeConfig, _first


class PrecedenceHelperTests(unittest.TestCase):
    def test_first_set_value_wins(self):
        self.assertEqual(_first(None, "", 0, "db", "env"), "db")

    def test_falls_through_unset_values(self):
        self.assertEqual(_first(None, "", 0, "env"), "env")

    def test_all_unset_is_none(self):
        self.assertIsNone(_first(None, "", 0))

    def test_zero_counts_as_unset(self):
        # max_turns=0 means "no limit configured", not "zero turns".
        self.assertEqual(_first(0, 40), 40)


class ConfigShapeTests(unittest.TestCase):
    def test_both_agents_are_configurable_separately(self):
        cfg = AgentModeConfig()
        for field in ("model", "effort", "max_budget_usd", "max_turns"):
            self.assertTrue(hasattr(cfg, field))
        for field in (
            "analyst_model",
            "analyst_effort",
            "analyst_budget_usd",
            "analyst_max_turns",
        ):
            self.assertTrue(hasattr(cfg, field), field)

    def test_defaults_are_safe(self):
        cfg = AgentModeConfig()
        self.assertFalse(cfg.enabled)
        self.assertFalse(cfg.allow_frontend_build)
        self.assertTrue(cfg.ensure_packages)
        self.assertEqual(cfg.source, "env")


if __name__ == "__main__":
    unittest.main()


class SettingsPayloadSerializationTests(unittest.TestCase):
    """`get_api_response` serializes with a bare `json.dumps()`, so any
    Decimal or datetime reaching it 500s the request. This broke every save
    of the settings form until it was caught."""

    def test_jsonable_coerces_decimal_and_datetime(self):
        import datetime as dt
        from decimal import Decimal

        from zango.api.platform.agent_mode_admin.v1.views import _jsonable

        self.assertEqual(_jsonable(Decimal("30.0000")), 30.0)
        self.assertEqual(
            _jsonable(dt.datetime(2026, 9, 15, 10, 0)), "2026-09-15T10:00:00"
        )
        self.assertEqual(_jsonable("claude-opus-5"), "claude-opus-5")
        self.assertIsNone(_jsonable(None))

    def test_settings_payload_is_serializable(self):
        import json
        from decimal import Decimal

        from zango.api.platform.agent_mode_admin.v1.views import _jsonable

        payload = {
            "max_budget_usd": _jsonable(Decimal("30")),
            "analyst_budget_usd": _jsonable(Decimal("1.5")),
            "max_turns": None,
        }
        json.dumps({"success": True, "response": payload})

    def test_whole_payload_is_coerced_recursively(self):
        # Field-level coercion was applied once and then silently lost when
        # the formatter reflowed the line. Coercing at the boundary means a
        # new field cannot reintroduce the failure.
        import json
        from decimal import Decimal

        from zango.api.platform.agent_mode_admin.v1.views import _coerce

        payload = {
            "settings": {
                "max_budget_usd": Decimal("25"),
                "nested": {"x": Decimal("1.5")},
            },
            "list": [Decimal("2"), {"y": Decimal("3")}],
            "plain": "ok",
        }
        json.dumps(_coerce(payload))

    def test_coercion_is_depth_bounded(self):
        from zango.api.platform.agent_mode_admin.v1.views import _coerce

        deep = cur = {}
        for _ in range(40):
            cur["n"] = {}
            cur = cur["n"]
        _coerce(deep)  # must not recurse without bound

    def test_raw_decimal_would_still_raise(self):
        # Guards the assumption the coercion rests on.
        import json
        from decimal import Decimal

        with self.assertRaises(TypeError):
            json.dumps({"x": Decimal("1")})


class LiveReloadTests(unittest.TestCase):
    """Settings must apply without restarting the worker.

    load_config() reads the row on every call, and every call site is inside
    the task at run start — so a change lands on the next run. If a cache is
    ever added here, this contract breaks silently and the UI's promise
    becomes a lie.
    """

    def test_load_config_is_not_cached(self):
        import inspect

        from zango.apps.agent_mode import config

        source = inspect.getsource(config.load_config)
        for decorator in ("lru_cache", "cache", "cached_property"):
            self.assertNotIn(decorator, source)

    def test_call_sites_resolve_config_at_run_time(self):
        # Reading config at import time would freeze it for the process.
        import inspect

        from zango.apps.agent_mode import options, requirements

        for module, func in (
            (options, "build_agent_options"),
            (requirements, "build_analyst_options"),
        ):
            source = inspect.getsource(getattr(module, func))
            self.assertIn("load_config()", source, f"{func} must resolve per run")
