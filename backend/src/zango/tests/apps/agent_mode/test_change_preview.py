"""A change request keeps the app's current preview: what changed is marked, the current app can be shown
for comparison, and the current app is never written by the change."""

import copy
import json

from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from zango.apps.agent_mode import prototype_changes as pc
from zango.apps.agent_mode.models import RequirementStatus


def manifest(*screens):
    return json.dumps({"screens": [{"id": i, "title": t} for i, t in screens]})


BASE = {
    "manifest.json": manifest(("openings", "Openings"), ("candidates", "Candidates")),
    "screens/openings.js": "A",
    "screens/candidates.js": "B",
    "shell.js": "menu v1",
    "app.css": "css",
}


class ScreenDiff(SimpleTestCase):
    def test_identical_has_no_changes(self):
        d = pc.screen_diff(BASE, copy.deepcopy(BASE))
        self.assertEqual((d["changed"], d["added"], d["removed"], d["shared"]), ([], [], [], []))

    def test_changed_added_removed_and_shared(self):
        new = {
            **BASE,
            "manifest.json": manifest(("openings", "Openings"), ("my_downloads", "My Downloads")),
            "screens/openings.js": "A2",
            "screens/my_downloads.js": "D",
            "shell.js": "menu v2",
        }
        del new["screens/candidates.js"]
        d = pc.screen_diff(BASE, new)
        self.assertEqual(d["changed"], [{"id": "openings", "title": "Openings"}])
        self.assertEqual(d["added"], [{"id": "my_downloads", "title": "My Downloads"}])
        self.assertEqual(d["removed"], [{"id": "candidates", "title": "Candidates"}])
        self.assertEqual(d["shared"], ["shell.js"])  # the menu changed; the manifest alone is not "shared"

    def test_a_missing_manifest_still_names_screens_by_id(self):
        d = pc.screen_diff({"screens/a.js": "1"}, {"screens/a.js": "2"})
        self.assertEqual(d["changed"], [{"id": "a", "title": "a"}])


def req(status=RequirementStatus.GATHERING, parts=None, mode="open"):
    return SimpleNamespace(pk=2, status=status, preview_mode=mode, prototype_parts=parts if parts is not None else {})


class Describe(SimpleTestCase):
    base = SimpleNamespace(object_uuid="u1", prototype_revision=28, title="Initial build", prototype_parts=BASE)

    def run_describe(self, r, base="default"):
        with mock.patch.object(pc, "current_app_requirement", lambda requirement=None: self.base if base == "default" else base):
            return pc.describe(r)

    def test_untouched_change_says_no_changes(self):
        d = self.run_describe(req(parts=copy.deepcopy(BASE)))
        self.assertFalse(d["has_changes"])
        self.assertEqual(d["baseline"], {"uuid": "u1", "revision": 28, "title": "Initial build"})

    def test_an_edited_screen_is_reported(self):
        d = self.run_describe(req(parts={**BASE, "screens/openings.js": "A2"}))
        self.assertTrue(d["has_changes"])
        self.assertEqual([x["id"] for x in d["changed"]], ["openings"])

    def test_nothing_to_compare_for_a_first_version(self):
        self.assertIsNone(self.run_describe(req(parts=BASE), base=None))

    def test_not_for_an_approved_or_closed_requirement_or_kit_mode(self):
        self.assertIsNone(self.run_describe(req(status=RequirementStatus.APPROVED, parts=BASE)))
        self.assertIsNone(self.run_describe(req(parts=BASE, mode="kit")))

    def test_the_current_app_is_never_written(self):
        before = copy.deepcopy(self.base.prototype_parts)
        self.run_describe(req(parts={**BASE, "screens/openings.js": "A2"}))
        self.assertEqual(self.base.prototype_parts, before)


class CurrentApp(SimpleTestCase):
    def test_it_is_the_last_approved_requirement_other_than_this_one(self):
        qs = mock.MagicMock()
        with mock.patch.object(pc.AgentRequirement, "objects", qs):
            pc.current_app_requirement(SimpleNamespace(pk=2))
        qs.filter.assert_called_once_with(status=RequirementStatus.APPROVED)
        qs.filter.return_value.exclude.assert_called_once_with(pk=2)
        qs.filter.return_value.exclude.return_value.order_by.assert_called_once_with("-approved_at", "-created_at")


class Headline(SimpleTestCase):
    def d(self, **kw):
        return {"changed": [], "added": [], "removed": [], "shared": [], **kw}

    def t(self, *names):
        return [{"id": n, "title": n} for n in names]

    def test_names_what_changed(self):
        self.assertEqual(pc.headline(self.d(added=self.t("My Downloads"))), "Adds My Downloads")
        self.assertEqual(pc.headline(self.d(changed=self.t("Openings", "Candidates"))), "Updates Openings and Candidates")
        self.assertEqual(
            pc.headline(self.d(added=self.t("A"), changed=self.t("B"), removed=self.t("C"))),
            "Adds A, updates B, removes C",
        )

    def test_long_lists_are_shortened(self):
        self.assertEqual(pc.headline(self.d(changed=self.t("A", "B", "C", "D"))), "Updates A, B and 2 more")

    def test_shared_only_and_nothing(self):
        self.assertEqual(pc.headline(self.d(shared=["app.css"])), "Updates the app's look and settings")
        self.assertEqual(pc.headline(self.d()), "")

    def test_a_change_is_retitled_but_not_when_nothing_changed(self):
        req = SimpleNamespace(
            preview_mode="open",
            prototype_parts={**BASE, "screens/openings.js": "A2"},
            title="Recruiters can export lists, but there's nowhere",
        )
        base = SimpleNamespace(prototype_parts=BASE)
        with mock.patch.object(pc, "current_app_requirement", return_value=base):
            self.assertTrue(pc.retitle_change(req))
            self.assertEqual(req.title, "Updates Openings")
            req.prototype_parts = copy.deepcopy(BASE)
            self.assertFalse(pc.retitle_change(req))
            self.assertEqual(req.title, "Updates Openings")
