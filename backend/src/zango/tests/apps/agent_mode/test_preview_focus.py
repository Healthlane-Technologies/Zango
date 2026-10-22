"""Where the user was in the preview goes with their message (agent_mode/preview_focus.py)."""

import unittest

from pathlib import Path

import zango

from zango.apps.agent_mode.preview_focus import clean_focus, focus_note


POINTED = {
    "role": "Procurement Manager",
    "page": "vendor_360",
    "title": "Pioneer Pharma",
    "path": "/pages/@vendor_360",
    "record": {"entity": "vendor", "id": 1, "label": "Pioneer Pharma"},
    "tab": {"code": "risk", "label": "Risk", "path": "/detail_views/@vendor_360/tabs/@risk"},
    "pointed": {"path": "/detail_views/@vendor_360/stats/0", "label": "Open POs", "text": "3"},
}


class CleanFocusTests(unittest.TestCase):
    def test_keeps_the_known_shape(self):
        out = clean_focus(POINTED)
        self.assertEqual(out["role"], "Procurement Manager")
        self.assertEqual(out["record"], {"entity": "vendor", "id": "1", "label": "Pioneer Pharma"})
        self.assertEqual(out["tab"], {"label": "Risk", "path": "/detail_views/@vendor_360/tabs/@risk"})
        self.assertEqual(out["pointed"]["path"], "/detail_views/@vendor_360/stats/0")

    def test_drops_what_the_browser_should_not_send(self):
        out = clean_focus({**POINTED, "script": "<x>", "role": {"nested": 1}, "title": "a" * 999})
        self.assertNotIn("script", out)
        self.assertNotIn("role", out)
        self.assertEqual(len(out["title"]), 160)

    def test_a_pointer_needs_a_spec_path(self):
        out = clean_focus({"page": "tasks", "pointed": {"path": "javascript:alert(1)", "label": "x"}})
        self.assertNotIn("pointed", out)

    def test_nothing_useful_is_nothing(self):
        self.assertEqual(clean_focus(None), {})
        self.assertEqual(clean_focus("tasks"), {})
        self.assertEqual(clean_focus({"role": "Manager"}), {})


class FocusNoteTests(unittest.TestCase):
    def test_a_pointer_tells_the_analyst_what_this_means(self):
        note = focus_note(clean_focus(POINTED))
        self.assertTrue(note.startswith("\n\n[Preview: the user was looking at"))
        self.assertIn('"Pioneer Pharma" (/pages/@vendor_360) as Procurement Manager', note)
        self.assertIn('tab "Risk" (/detail_views/@vendor_360/tabs/@risk)', note)
        self.assertIn("They pointed at Open POs showing \"3\": /detail_views/@vendor_360/stats/0", note)
        self.assertTrue(note.endswith("]"))

    def test_without_a_pointer_it_says_where_they_were(self):
        note = focus_note(clean_focus({"role": "Manager", "page": "tasks", "title": "Tasks", "path": "/pages/@tasks"}))
        self.assertEqual(note, '\n\n[Preview: the user was looking at "Tasks" (/pages/@tasks) as Manager.]')

    def test_pointing_at_an_unsketched_custom_screen_says_so(self):
        doc = {"detail_views": [{"code": "vendor_360", "sidebar": [
            {"type": "fields"}, {"type": "custom", "title": "Next steps", "text": "Who does what next."}]}]}
        focus = clean_focus({**POINTED, "pointed": {"path": "/detail_views/@vendor_360/sidebar/1", "label": "Next steps"}})
        self.assertIn("no `preview` sketch", focus_note(focus, doc))
        doc["detail_views"][0]["sidebar"][1]["preview"] = "return ctx.ui.empty('x');"
        self.assertNotIn("no `preview` sketch", focus_note(focus, doc))
        self.assertNotIn("no `preview` sketch", focus_note(focus))

    def test_no_focus_no_note(self):
        self.assertEqual(focus_note({}), "")
        self.assertEqual(focus_note(None), "")

    def test_a_multipart_focus_arrives_as_json_text(self):
        raw = '{"page": "Referrals", "pointed": {"path": "/pages/0", "label": "New Referral"}}'
        out = clean_focus(raw)
        self.assertEqual(out["page"], "Referrals")
        self.assertEqual(out["pointed"]["label"], "New Referral")
        self.assertEqual(clean_focus("not json"), {})


class WiringTests(unittest.TestCase):
    """The message view stores the cleaned focus; the turn reads it under the message."""

    SRC = Path(zango.__file__).resolve().parent

    def test_the_message_view_cleans_and_stores_the_focus(self):
        views = (self.SRC / "api/platform/agent_mode/v1/views.py").read_text()
        self.assertIn('clean_focus(request.data.get("focus"))', views)
        self.assertIn("preview_focus=focus or {}", views)

    def test_a_new_change_stores_the_focus_on_its_first_message(self):
        views = (self.SRC / "api/platform/agent_mode/v1/views.py").read_text()
        self.assertIn(
            'requirement, prompt, clean_focus(request.data.get("focus"))', views
        )

    def test_the_turn_appends_the_note_to_the_message(self):
        tasks = (self.SRC / "apps/agent_mode/tasks.py").read_text()
        self.assertIn("last_user.content + focus_note(last_user.preview_focus, _plain_spec(req))", tasks)
