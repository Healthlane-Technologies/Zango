"""The person who made the app sees progress, never failures (the chat's build card).

Regression (run 8): the run ended "partial" with "checks still fail after 2 fix round(s): api (2),
ui (19), design (8), scenarios (2)", most of them our own test code's bugs.
"""

import json
import tempfile
import unittest

from pathlib import Path

from zango.apps.agent_mode.studio_build import LayerResult
from zango.apps.agent_mode.studio_status import kind, sort_failures, user_status, without_harness


SPEC = {
    "app": {"name": "Sponsorships"},
    "roles": {"Requester": {}, "Finance": {}},
    "pages": {"requests": {"title": "Requests", "type": "crud", "entity": "request"},
              "payments": {"title": "Payments", "type": "crud", "entity": "payment"}},
    "entities": {"request": {"name": "Request", "list_page": "requests", "table": {"add_button": "New request"}},
                 "payment": {"name": "Payment", "list_page": "payments"}},
    "detail_views": {},
}
RESULTS = [
    {"id": "ui.flow.request.create.requester", "status": "pass", "role": "Requester",
     "title": "Request: create from the list page"},
    {"id": "ui.flow.payment.upload.requester", "status": "pass", "role": "Requester",
     "title": "Payment: Upload from the 360"},
    {"id": "ui.flow.payment.release.finance", "status": "fail", "role": "Finance",
     "title": "Payment: Release payment from the 360"},
    {"id": "design.parity.proto.requests.requester", "status": "pass"},
]


def layer(name, *failures):
    return {name: {"status": "fail" if failures else "pass", "failures": list(failures)}}


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        zas = Path(self.tmp.name) / ".zas"
        zas.mkdir()
        (zas / "spec.resolved.json").write_text(json.dumps(SPEC))
        (zas / "test_results.json").write_text(json.dumps({"results": RESULTS}))
        self.ws = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_our_own_test_bugs_are_not_the_apps(self):
        f = {"id": "design.tree.x", "layer": "design", "detail": "TypeError(\"'<' not supported\")"}
        self.assertEqual(kind(f), "harness")
        card = user_status(self.ws, layer("design", f), True, active=False)
        self.assertEqual(card["state"], "ready")

    def test_a_record_that_cannot_be_created_is_still_building(self):
        f = {"id": "ui.flow.request.create.requester", "layer": "ui", "detail": "the server answered HTTP 500"}
        card = user_status(self.ws, layer("ui", f), True, active=True)
        self.assertEqual(card["state"], "building")
        self.assertEqual(card["roles"], [])
        self.assertEqual(user_status(self.ws, {}, False, active=True)["state"], "building")

    def test_details_left_are_finishing_touches_by_screen_never_failures(self):
        f = {"id": "ui.flow.payment.release.finance", "layer": "ui", "spec_path": "entities.payment.workflow",
             "detail": "'Release payment' is disabled"}
        card = user_status(self.ws, layer("ui", f), True, active=True)
        self.assertEqual(card["state"], "finishing")
        self.assertEqual(card["finishing"], "Finishing touches on Payments")
        text = json.dumps(card).lower()
        for word in ("fail", "error", "disabled", "broken", "missing"):
            self.assertNotIn(word, text)
        self.assertIn("Our team", user_status(self.ws, layer("ui", f), True, active=False)["finishing"])

    def test_roles_show_only_what_they_did(self):
        card = user_status(self.ws, {}, True, active=False)
        self.assertEqual(card["roles"], [{"role": "Requester", "steps": ["New request", "Upload payment"]}])
        self.assertEqual(card["tried"], {"steps": 3, "roles": 2, "screens": 1})

    def test_the_agents_own_broken_script_is_never_the_users(self):
        f = {"id": "scenario.H-07", "layer": "scenarios",
             "detail": "AttributeError(\"'tuple'\") File \".zas/test_scenarios.py\", line 19"}
        self.assertEqual(kind(f), "test")
        self.assertEqual(sort_failures(layer("scenarios", f))["polish"], [])

    def test_harness_failures_leave_the_verdict_and_the_brief(self):
        L = {"design": LayerResult(name="design", status="fail", failures=[
            {"id": "design.tree.x", "detail": "TypeError('x')"}])}
        clean = without_harness(L)
        self.assertEqual(clean["design"].status, "pass")
        self.assertEqual(clean["design"].failures, [])
        self.assertEqual(L["design"].status, "fail")  # the report keeps it


if __name__ == "__main__":
    unittest.main()
