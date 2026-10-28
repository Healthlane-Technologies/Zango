"""The bring-up's platform steps: cron lines the platform accepts, and a dev server that is restarting.

Regression (zango_isn_hcp): `# zas:schedule */5 * * * *` came back HTTP 500 "Invalid cron expression"
in two fix rounds; the third bring-up started 7 s after an edit and the restarting server refused
the login, so the build ended with every test layer "not run".
"""

import sys
import unittest

from pathlib import Path
from unittest import mock

import requests

from zango.apps.shared.app_templates.services.generic import studio_plugin_dir
from zango.apps.tasks.utils import validate_cron_input


SKILL = Path(studio_plugin_dir()) / "skills" / "zango-app-studio"
if str(SKILL / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL / "scripts"))

import zango_platform as ZP  # noqa: E402


class CronTests(unittest.TestCase):
    def test_steps_and_ranges_become_lists_the_platform_accepts(self):
        line = {"minute": "*/5", "hour": "9-17", "day_of_month": "*", "month_of_year": "*", "day_of_week": "1-5"}
        exp = {k: ZP.cron_field(line[k], lo, hi) for k, lo, hi in ZP.CRON_FIELDS}
        self.assertEqual(exp["minute"], "0,5,10,15,20,25,30,35,40,45,50,55")
        self.assertEqual(exp["day_of_week"], "1,2,3,4,5")
        self.assertTrue(validate_cron_input(exp))

    def test_plain_lines_are_unchanged(self):
        self.assertEqual(ZP.cron_field("0", 0, 59), "0")
        self.assertEqual(ZP.cron_field("0,30", 0, 59), "0,30")
        self.assertEqual(ZP.cron_field("*", 0, 59), "*")
        self.assertEqual(ZP.cron_field("0-30/10", 0, 59), "0,10,20,30")

    def test_out_of_range_is_refused_before_the_platform_sees_it(self):
        for value, lo, hi in (("60", 0, 59), ("*/0", 0, 59), ("0", 1, 6), ("7", 1, 6), ("mon", 1, 6)):
            with self.assertRaises(ValueError):
                ZP.cron_field(value, lo, hi)


class ReachableTests(unittest.TestCase):
    def test_a_restarting_server_is_waited_for(self):
        P = ZP.Platform.__new__(ZP.Platform)
        P.url, P.s = "http://localhost:8000", mock.Mock()
        P.s.get.side_effect = [requests.ConnectionError("refused"), requests.ConnectionError("refused"), "page"]
        with mock.patch("time.sleep") as nap:
            self.assertEqual(P._reachable(), "page")
        self.assertEqual(nap.call_count, 2)

    def test_a_server_that_stays_down_is_a_clear_error(self):
        P = ZP.Platform.__new__(ZP.Platform)
        P.url, P.s = "http://localhost:8000", mock.Mock()
        P.s.get.side_effect = requests.ConnectionError("refused")
        with mock.patch("time.sleep"), self.assertRaisesRegex(ZP.PlatformError, "still refusing"):
            P._reachable(wait=0)


if __name__ == "__main__":
    unittest.main()
