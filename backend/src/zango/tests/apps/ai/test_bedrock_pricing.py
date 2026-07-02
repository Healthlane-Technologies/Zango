"""
Unit tests for zango.ai.bedrock_pricing — the AWS Price List parsing used by
the off-request pricing refresh task.

boto3 / the pricing client are mocked; these tests never touch AWS and never
hit the DB. They cover:
  - model-ID → match-token derivation and conservative row matching
  - input/output/cache classification of price rows
  - per-token USD → per-MTok normalisation
  - fetch_bedrock_rates() returns {} when settings creds are absent
  - fetch_bedrock_rates() parses a mocked GetProducts response correctly
"""

import json

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from zango.ai import bedrock_pricing as bp


class MatchTokenTest(SimpleTestCase):
    def test_tokens_include_version_date_and_family(self):
        toks = bp._model_match_tokens("anthropic.claude-sonnet-4-5-20250929-v1:0")
        self.assertIn("20250929", toks)
        self.assertIn("claudesonnet45", toks)

    def test_tokens_without_date(self):
        toks = bp._model_match_tokens("amazon.nova-pro-v1:0")
        self.assertEqual(toks, ["novaprov1"])

    def test_row_matches_requires_all_tokens(self):
        toks = bp._model_match_tokens("anthropic.claude-sonnet-4-5-20250929-v1:0")
        good = bp._normalize(json.dumps({"model": "Claude Sonnet 4.5"}) + "20250929")
        # Missing the date → no match (conservative).
        bad = bp._normalize(json.dumps({"model": "Claude Sonnet 4.5"}))
        self.assertTrue(bp._row_matches_model(good, toks))
        self.assertFalse(bp._row_matches_model(bad, toks))

    def test_no_tokens_never_matches(self):
        self.assertFalse(bp._row_matches_model("anything", []))


class ClassifyTest(SimpleTestCase):
    def test_input_and_output(self):
        self.assertEqual(bp._classify_usagetype("APS3-InputTokens", ""), "input")
        self.assertEqual(bp._classify_usagetype("APS3-OutputTokens", ""), "output")

    def test_cache_rows_ignored(self):
        # A cache-write row's usagetype still contains "Input" — must be ignored.
        self.assertIsNone(
            bp._classify_usagetype("APS3-CacheWriteInputTokens", "")
        )
        self.assertIsNone(bp._classify_usagetype("", "Cache read tokens"))

    def test_unrelated_row(self):
        self.assertIsNone(bp._classify_usagetype("APS3-Storage", "Provisioned"))


class ParsePriceDimensionTest(SimpleTestCase):
    def test_extracts_usd(self):
        dim = {"pricePerUnit": {"USD": "0.000003"}}
        self.assertAlmostEqual(bp._parse_price_dimension(dim), 0.000003)

    def test_missing_usd(self):
        self.assertIsNone(bp._parse_price_dimension({"pricePerUnit": {}}))
        self.assertIsNone(bp._parse_price_dimension({}))


class FetchBedrockRatesTest(SimpleTestCase):
    def test_returns_empty_without_credentials(self):
        with patch.object(bp, "_get_settings_credentials", return_value=(None, None)):
            self.assertEqual(bp.fetch_bedrock_rates(), {})

    def test_parses_mocked_get_products(self):
        # Build a fake GetProducts page with input + output rows for Sonnet 3.5 v2.
        bare_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

        def _row(usagetype, usd):
            product = {
                "product": {
                    "attributes": {
                        "usagetype": usagetype,
                        "model": "Claude 3.5 Sonnet",
                    }
                },
                # Add the version date so the conservative matcher matches.
                "terms": {
                    "OnDemand": {
                        "sku.1": {
                            "priceDimensions": {
                                "sku.1.dim": {
                                    "unit": "tokens",
                                    "pricePerUnit": {"USD": usd},
                                    "description": f"{usagetype} 20241022",
                                }
                            }
                        }
                    }
                },
            }
            # Inject the date into the attributes blob so matching succeeds.
            product["product"]["attributes"]["operation"] = "20241022"
            return json.dumps(product)

        page = {
            "PriceList": [
                _row("USE1-InputTokens", "0.000003"),   # $3 / Mtok
                _row("USE1-OutputTokens", "0.000015"),  # $15 / Mtok
            ]
        }

        fake_paginator = MagicMock()
        fake_paginator.paginate.return_value = [page]
        fake_client = MagicMock()
        fake_client.get_paginator.return_value = fake_paginator

        with patch.object(
            bp, "_get_settings_credentials", return_value=("AK", "SK")
        ), patch.object(bp, "_build_pricing_client", return_value=fake_client), patch(
            "builtins.__import__", side_effect=__import__
        ):
            rates = bp.fetch_bedrock_rates(regions=["us-east-1"])

        self.assertIn("us-east-1", rates)
        self.assertIn(bare_id, rates["us-east-1"])
        entry = rates["us-east-1"][bare_id]
        self.assertAlmostEqual(entry["input_per_mtok"], 3.0)
        self.assertAlmostEqual(entry["output_per_mtok"], 15.0)

    def test_get_products_failure_degrades_to_empty(self):
        fake_client = MagicMock()
        fake_client.get_paginator.side_effect = Exception("AccessDenied")
        with patch.object(
            bp, "_get_settings_credentials", return_value=("AK", "SK")
        ), patch.object(bp, "_build_pricing_client", return_value=fake_client):
            rates = bp.fetch_bedrock_rates(regions=["us-east-1"])
        self.assertEqual(rates, {})
