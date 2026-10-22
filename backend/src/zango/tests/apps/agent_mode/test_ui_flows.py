"""The UI layer's `flows` group: which moves it walks, and what it flags without a browser.

The browser steps themselves run against a live app (zas_test.ui --only flows); these cover the
choices made before a page opens.
"""

import sys
import unittest

from pathlib import Path

from zango.apps.shared.app_templates.services.generic import studio_plugin_dir

SCRIPTS = Path(studio_plugin_dir()) / "skills" / "zango-app-studio" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from zas_test import flows  # noqa: E402


def t(name, frm, to, roles=("Executive",), system=False):
    return {"name": name, "from": list(frm), "to": to, "roles": list(roles), "system": system}


REFERRAL = {
    "initial": "new",
    "transitions": [
        t("log_contact", ["new"], "contacted"),
        t("start", ["contacted"], "started"),
        t("assess", ["started"], "assessing"),
        t("approve", ["assessing"], "approved"),
        t("decline", ["assessing"], "declined"),
    ],
}


def anyone(_t):
    return True


class LongestPathTests(unittest.TestCase):
    def names(self, wf, roles_ok=anyone):
        return [x["name"] for x in flows.longest_path(wf, roles_ok)]

    def test_walks_the_longest_chain_from_the_initial_status(self):
        # approve and decline are equally long; the first listed wins, decline runs on its own record
        self.assertEqual(self.names(REFERRAL), ["log_contact", "start", "assess", "approve"])

    def test_a_loop_is_walked_once(self):
        wf = {"initial": "pending", "transitions": [
            t("flag_delay", ["pending", "delayed"], "delayed"),
            t("mark_disbursed", ["pending", "delayed"], "disbursed"),
            t("mark_not_done", ["pending", "delayed"], "not_done"),
        ]}
        self.assertEqual(self.names(wf), ["flag_delay", "mark_disbursed"])

    def test_system_moves_are_left_to_the_scheduler(self):
        wf = {"initial": "processing", "transitions": [
            t("complete", ["processing"], "ready", roles=(), system=True),
            t("regenerate", ["expired"], "processing", roles=("Admin",)),
        ]}
        self.assertEqual(self.names(wf), [])

    def test_moves_no_logged_in_role_may_run_are_skipped(self):
        wf = {"initial": "new", "transitions": [t("a", ["new"], "x", roles=("Finance",)), t("b", ["new"], "y")]}
        self.assertEqual(self.names(wf, lambda tr: "Executive" in tr["roles"]), ["b"])


class BadDefaultTests(unittest.TestCase):
    def setUp(self):
        self.F = flows.Flows.__new__(flows.Flows)  # bad_defaults reads only the form

    def test_a_callable_model_default_served_as_its_repr_is_flagged(self):
        form = {"json_schema": {"properties": {
            "disbursement_date": {"type": "string", "default": "<function localdate at 0x10317cdc0>"},
            "amount": {"type": "number", "default": 1500},
            "note": {"type": "string", "default": "Called the patient"},
        }}}
        probs = self.F.bad_defaults(form)
        self.assertEqual(len(probs), 1)
        self.assertIn("disbursement_date", probs[0])

    def test_ordinary_text_with_angle_brackets_is_not_flagged(self):
        form = {"json_schema": {"properties": {"tpl": {"type": "string", "default": "<b>Hello</b>"}}}}
        self.assertEqual(self.F.bad_defaults(form), [])


if __name__ == "__main__":
    unittest.main()
