"""Free design: the brand colour is the YAML's app.theme.primary, never a hex in the prototype.

The preview sets --brand from it, app.design's brand shades follow it, and the default-look
example derives every brand shade from var(--brand).
"""

import json
import re
import unittest

from pathlib import Path

from zango.apps.agent_mode.prototype import assemble, design_tokens, theme_brand


EXAMPLE = (
    Path(__file__).resolve().parents[3]
    / "apps/agent_mode/skill_plugin/skills/zango-prototype/references/example"
)
PARTS = {
    "manifest.json": json.dumps({"title": "T", "screens": [{"id": "home"}]}),
    "tokens.css": ":root{--brand:#4F46E5;--brand-soft:color-mix(in srgb,var(--brand) 8%,#fff);--page:#F9FAFB}",
}


def example_parts() -> dict:
    return {
        str(p.relative_to(EXAMPLE)): p.read_text()
        for p in EXAMPLE.rglob("*")
        if p.is_file()
    }


class ThemeBrandTests(unittest.TestCase):
    def test_reads_primary(self):
        self.assertEqual(theme_brand('app:\n  theme: {primary: "#0F766E"}\n'), "#0F766E")

    def test_ignores_missing_or_bad_values(self):
        for spec in ("", "app: {}", "app:\n  theme: {primary: teal}\n", ": ["):
            self.assertIsNone(theme_brand(spec), spec)


class AssembleBrandTests(unittest.TestCase):
    def test_brand_overrides_tokens_after_the_parts_css(self):
        html = assemble(PARTS, [], "#0f766e")
        self.assertIn('<style data-zas="theme">:root{--brand:#0f766e}</style>', html)
        self.assertLess(html.index('data-part="tokens.css"'), html.index('data-zas="theme"'))

    def test_no_brand_no_override(self):
        self.assertNotIn('data-zas="theme"', assemble(PARTS, []))
        self.assertNotIn('data-zas="theme"', assemble(PARTS, [], "red;}body{x"))


class DesignTokensBrandTests(unittest.TestCase):
    def test_derived_shades_follow_the_brand(self):
        tokens = design_tokens(PARTS, "#0f766e")["tokens"]
        self.assertEqual(tokens["brand"], "#0f766e")
        self.assertIn("#0f766e", tokens["brand-soft"])
        self.assertEqual(tokens["page"], "#F9FAFB")

    def test_without_brand_the_fallback_stays(self):
        self.assertEqual(design_tokens(PARTS)["tokens"]["brand"], "#4F46E5")


class ExampleHasNoBrandHexTests(unittest.TestCase):
    """The agent copies the example; a brand hex in it would be copied too."""

    def test_brand_declared_once_and_derived(self):
        parts = example_parts()
        tokens = design_tokens(parts, "#123456")["tokens"]
        for name in ("brand", "brand-strong", "brand-soft"):
            self.assertIn("#123456", tokens[name], name)

    def test_no_part_hard_codes_the_fallback(self):
        for path, text in example_parts().items():
            if path == "tokens.css":
                continue
            self.assertIsNone(re.search(r"#4f46e5", text, re.I), path)


class SetBrandTests(unittest.TestCase):
    """The colour picker's save: app.theme.primary and the brand tokens derived from --brand."""

    SPEC = (
        "app:\n"
        "  code: t  # keep me\n"
        "  theme: {primary: '#4F46E5'}\n"
        "  design:\n"
        "    tokens: {brand: '#4F46E5', brand-soft: 'color-mix(in srgb,#4F46E5 8%,#fff)', page: '#F9FAFB'}\n"
    )

    def _run(self, primary):
        from types import SimpleNamespace
        from unittest import mock

        from zango.apps.agent_mode import template_spec

        req = SimpleNamespace(spec_markdown=self.SPEC, prototype_parts=PARTS, draft_revision=3)
        saved = {}

        def save(r, text, base):
            saved.update(text=text, base=base)
            return 200, {}

        with mock.patch.object(template_spec, "_edit_blocked", return_value=None), mock.patch.object(
            template_spec, "save_manual", side_effect=save
        ):
            code, _ = template_spec.set_brand(req, primary)
        return code, saved

    def test_sets_primary_and_derived_tokens(self):
        from zango.apps.shared.app_templates.services.spec import yamlio

        code, saved = self._run("#0F766E")
        self.assertEqual(code, 200)
        self.assertEqual(saved["base"], 3)
        self.assertIn("# keep me", saved["text"])
        doc = yamlio.load_rt(saved["text"])
        self.assertEqual(doc["app"]["theme"]["primary"], "#0f766e")
        tokens = doc["app"]["design"]["tokens"]
        self.assertEqual(tokens["brand"], "#0f766e")
        self.assertIn("#0f766e", tokens["brand-soft"])
        self.assertEqual(tokens["page"], "#F9FAFB")

    def test_refuses_a_non_colour(self):
        code, saved = self._run("teal")
        self.assertEqual(code, 400)
        self.assertEqual(saved, {})


if __name__ == "__main__":
    unittest.main()
