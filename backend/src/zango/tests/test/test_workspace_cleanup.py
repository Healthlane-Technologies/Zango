"""The test harness must not be able to delete a real app's source.

`ZangoAppBaseTestCase.clean_workspaces` once removed `BASE_DIR/workspaces`
outright. Django isolates the test database but not the filesystem, so a run
against any project whose BASE_DIR is not a throwaway test project wiped every
app on that machine — and the database was untouched afterwards, so nothing
looked wrong until someone opened an app.

These pin the blast radius: one workspace, the one the test made.
"""

import os
import shutil
import tempfile
import unittest

from pathlib import Path

from django.test import override_settings

from zango.test.cases import ZangoAppBaseTestCase


class _Tenant:
    def __init__(self, name):
        self.name = name


class _Case:
    """Enough of a test class for the classmethod to run against."""

    def __init__(self, tenant_name):
        self.tenant = _Tenant(tenant_name)


def _clean(case):
    # Unbound, so it can be driven with a stand-in for `cls`.
    return ZangoAppBaseTestCase.clean_workspaces.__func__(case)


class CleanWorkspacesTests(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.root = Path(self.base) / "workspaces"
        self.root.mkdir()
        # The workspace this "test" created, plus a real app beside it.
        (self.root / "testapp" / "modules").mkdir(parents=True)
        (self.root / "testapp" / "settings.json").write_text("{}")
        (self.root / "task_manager" / "modules").mkdir(parents=True)
        (self.root / "task_manager" / "settings.json").write_text('{"real": true}')
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)

    def _settings(self):
        return override_settings(BASE_DIR=self.base)

    def test_removes_the_workspace_the_test_created(self):
        with self._settings():
            _clean(_Case("testapp"))
        self.assertFalse((self.root / "testapp").exists())

    def test_leaves_every_other_app_alone(self):
        with self._settings():
            _clean(_Case("testapp"))
        self.assertTrue((self.root / "task_manager" / "settings.json").is_file())

    def test_never_removes_the_workspaces_tree(self):
        with self._settings():
            _clean(_Case("testapp"))
        self.assertTrue(self.root.is_dir())

    def test_a_missing_workspace_is_not_an_error(self):
        # A test that never initialised a workspace still tears down.
        with self._settings():
            _clean(_Case("never_created"))
        self.assertTrue(self.root.is_dir())

    def test_refuses_to_delete_the_tree_itself(self):
        # An empty tenant name resolves straight back to the root.
        with self._settings(), self.assertRaises(RuntimeError):
            _clean(_Case(""))
        self.assertTrue((self.root / "task_manager").is_dir())

    def test_refuses_to_escape_the_tree(self):
        with self._settings(), self.assertRaises(RuntimeError):
            _clean(_Case(".."))
        self.assertTrue(self.root.is_dir())
        self.assertTrue(os.path.isdir(self.base))

    def test_refuses_an_absolute_path(self):
        outside = Path(self.base) / "not-a-workspace"
        outside.mkdir()
        with self._settings(), self.assertRaises(RuntimeError):
            _clean(_Case(str(outside)))
        self.assertTrue(outside.is_dir())


if __name__ == "__main__":
    unittest.main()
