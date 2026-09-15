"""Redaction must hold: the API key must never reach an event row."""

import unittest

from zango.apps.agent_mode.credentials import (
    REDACTED,
    clear_registered_secrets,
    redact,
    redact_obj,
    register_secret,
)


class RedactionTests(unittest.TestCase):
    def setUp(self):
        clear_registered_secrets()

    def tearDown(self):
        clear_registered_secrets()

    def test_registered_secret_is_redacted(self):
        register_secret("sk-ant-super-secret-value-1234567890")
        out = redact("key is sk-ant-super-secret-value-1234567890 ok")
        self.assertNotIn("super-secret-value", out)
        self.assertIn(REDACTED, out)

    def test_unregistered_but_secret_shaped_is_redacted(self):
        # Defends against a key we were never told about.
        out = redact("export ANTHROPIC_API_KEY=sk-ant-abcdefghijklmnopqrstuvwxyz012345")
        self.assertNotIn("abcdefghijklmnop", out)
        self.assertIn(REDACTED, out)

    def test_overlapping_secrets_longest_first(self):
        register_secret("sk-ant-aaaaaaaaaaaaaaaa")
        register_secret("sk-ant-aaaaaaaaaaaaaaaa-extended-tail")
        out = redact("v=sk-ant-aaaaaaaaaaaaaaaa-extended-tail")
        self.assertNotIn("extended-tail", out)

    def test_short_values_are_not_registered(self):
        # Too collision-prone to blind-replace across all agent output.
        register_secret("abc")
        self.assertEqual(redact("abc def"), "abc def")

    def test_redact_obj_walks_nested_structures(self):
        register_secret("sk-ant-nested-secret-abcdefgh")
        payload = {
            "cmd": "echo sk-ant-nested-secret-abcdefgh",
            "items": [{"v": "sk-ant-nested-secret-abcdefgh"}],
            "n": 5,
            "ok": True,
        }
        out = redact_obj(payload)
        self.assertNotIn("nested-secret", str(out))
        self.assertEqual(out["n"], 5)
        self.assertIs(out["ok"], True)

    def test_non_strings_pass_through(self):
        self.assertEqual(redact(None), None)
        self.assertEqual(redact(7), 7)

    def test_recursion_is_bounded(self):
        deep = cur = {}
        for _ in range(50):
            cur["n"] = {}
            cur = cur["n"]
        redact_obj(deep)  # must not raise


if __name__ == "__main__":
    unittest.main()
