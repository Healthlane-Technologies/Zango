"""A change request opens on the app's current approved preview, not on an empty pane.

The console shows "No prototype yet" for prototype_revision 0, so seeding the prototype's parts and
hash without its revision left every change request looking blank while the parts were there.
"""

from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from zango.api.platform.agent_mode.v1 import views


def seeded(previous):
    req = SimpleNamespace(preview_mode="", prototype_parts={}, prototype_hash="", prototype_revision=0,
                          template_slug="x", template=None, spec_markdown="")
    qs = mock.MagicMock()
    qs.filter.return_value.order_by.return_value.only.return_value.first.return_value = previous
    with mock.patch.object(views.AgentRequirement, "objects", qs):
        views._seed_preview_mode(req, None)
    return req


class ChangeStartsOnCurrentPreview(SimpleTestCase):
    def test_copies_parts_hash_and_revision(self):
        prev = SimpleNamespace(prototype_parts={"a.html": "x"}, prototype_hash="h", prototype_revision=28)
        req = seeded(prev)
        self.assertEqual((req.prototype_parts, req.prototype_hash, req.prototype_revision), ({"a.html": "x"}, "h", 28))
        self.assertEqual(req.preview_mode, "open")

    def test_revision_is_never_zero_while_there_are_parts(self):
        prev = SimpleNamespace(prototype_parts={"a.html": "x"}, prototype_hash="h", prototype_revision=0)
        self.assertEqual(seeded(prev).prototype_revision, 1)

    def test_a_first_build_has_no_prototype(self):
        req = seeded(None)
        self.assertEqual((req.prototype_parts, req.prototype_revision), ({}, 0))
