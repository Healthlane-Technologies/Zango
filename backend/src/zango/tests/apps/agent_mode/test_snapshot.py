"""Snapshot, change detection and rollback.

Agent Mode writes into the live workspace with no diff gate, so the restore
path is the only undo — it gets tested like one.
"""

import os
import shutil
import tarfile
import tempfile
import unittest

from zango.apps.agent_mode.postrun import plan_steps, requires_restart
from zango.apps.agent_mode.snapshot import (
    FileChanges,
    create_snapshot,
    diff_manifest,
    prune_snapshots,
    restore_snapshot,
    workspace_manifest,
)


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ws-")
        write(self.root, "settings.json", '{"modules": []}')
        write(self.root, "patients/models.py", "class Patient: pass")
        write(self.root, "__pycache__/junk.pyc", "x")
        write(self.root, ".git/config", "x")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_excludes_noise(self):
        m = workspace_manifest(self.root)
        self.assertIn("settings.json", m)
        self.assertIn(os.path.join("patients", "models.py"), m)
        self.assertFalse([k for k in m if "__pycache__" in k or ".git" in k])

    def test_diff_detects_add_modify_delete(self):
        before = workspace_manifest(self.root)
        write(self.root, "vendors/models.py", "class Vendor: pass")
        write(self.root, "settings.json", '{"modules": ["vendors"]}')
        os.remove(os.path.join(self.root, "patients", "models.py"))
        changes = diff_manifest(before, workspace_manifest(self.root))
        self.assertIn(os.path.join("vendors", "models.py"), changes.added)
        self.assertIn("settings.json", changes.modified)
        self.assertIn(os.path.join("patients", "models.py"), changes.deleted)
        self.assertTrue(changes.any)

    def test_no_change_is_empty(self):
        before = workspace_manifest(self.root)
        self.assertFalse(diff_manifest(before, workspace_manifest(self.root)).any)


class SnapshotRoundTripTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ws-")
        self.dest = tempfile.mkdtemp(prefix="runs-")
        write(self.root, "settings.json", '{"v": 1}')
        write(self.root, "patients/models.py", "ORIGINAL")

    def tearDown(self):
        for d in (self.root, self.dest):
            shutil.rmtree(d, ignore_errors=True)

    def test_snapshot_then_restore_recovers_the_tree(self):
        snap = create_snapshot(self.root, self.dest, max_bytes=10**9)
        self.assertTrue(snap.ok, snap.skipped_reason)

        # Agent "damages" the workspace.
        write(self.root, "patients/models.py", "BROKEN")
        os.remove(os.path.join(self.root, "settings.json"))
        write(self.root, "junk/new.py", "junk")

        restore_snapshot(snap.path, self.root)

        with open(os.path.join(self.root, "patients", "models.py")) as fh:
            self.assertEqual(fh.read(), "ORIGINAL")
        self.assertTrue(os.path.exists(os.path.join(self.root, "settings.json")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "junk", "new.py")))

    def test_restore_keeps_the_displaced_tree(self):
        snap = create_snapshot(self.root, self.dest, max_bytes=10**9)
        write(self.root, "patients/models.py", "BROKEN")
        result = restore_snapshot(snap.path, self.root)
        prev = result["previous_tree"]
        self.assertTrue(prev and os.path.isdir(prev), "displaced tree was deleted")
        with open(os.path.join(prev, "patients", "models.py")) as fh:
            self.assertEqual(fh.read(), "BROKEN")
        shutil.rmtree(prev, ignore_errors=True)

    def test_oversize_workspace_skips_rather_than_blocks(self):
        snap = create_snapshot(self.root, self.dest, max_bytes=1)
        self.assertFalse(snap.ok)
        self.assertIn("ceiling", snap.skipped_reason)
        # The manifest is still captured, so change detection still works.
        self.assertTrue(snap.manifest)

    def test_restore_rejects_path_traversal_in_archive(self):
        evil = os.path.join(self.dest, "evil.tar.gz")
        outside = os.path.join(self.dest, "outside.txt")
        with open(outside, "w") as fh:
            fh.write("pwned")
        with tarfile.open(evil, "w:gz") as tar:
            tar.add(outside, arcname="../../escaped.txt")
        with self.assertRaises(ValueError):
            restore_snapshot(evil, self.root)

    def test_restore_missing_snapshot_raises(self):
        with self.assertRaises(FileNotFoundError):
            restore_snapshot(os.path.join(self.dest, "nope.tar.gz"), self.root)

    def test_prune_keeps_newest(self):
        runs = tempfile.mkdtemp(prefix="prune-")
        for i in range(7):
            os.makedirs(os.path.join(runs, f"run{i}"))
        removed = prune_snapshots(runs, keep=3)
        self.assertEqual(removed, 4)
        self.assertEqual(len(os.listdir(runs)), 3)
        shutil.rmtree(runs, ignore_errors=True)


class PostRunPlanTests(unittest.TestCase):
    def test_models_change_triggers_makemigration_and_migrate(self):
        steps = plan_steps(FileChanges(added=["patients/models.py"]), "MyApp")
        self.assertEqual([s for s, _ in steps], ["ws_makemigration", "ws_migrate"])
        self.assertIn("--noinput", steps[0][1])
        self.assertIn("--noinput", steps[1][1])

    def test_policies_change_triggers_ws_sync(self):
        steps = plan_steps(FileChanges(modified=["patients/policies.json"]), "MyApp")
        self.assertEqual([s for s, _ in steps], ["ws_sync"])

    def test_static_change_triggers_sync_static(self):
        steps = plan_steps(FileChanges(added=["static/js/app.js"]), "MyApp")
        self.assertEqual([s for s, _ in steps], ["sync_static"])

    def test_irrelevant_change_runs_nothing(self):
        self.assertEqual(plan_steps(FileChanges(modified=["README.md"]), "MyApp"), [])

    def test_migration_only_change_still_migrates(self):
        steps = plan_steps(FileChanges(added=["migrations/0002_x.py"]), "MyApp")
        self.assertEqual([s for s, _ in steps], ["ws_migrate"])

    def test_requires_restart(self):
        self.assertTrue(requires_restart(FileChanges(added=["a/models.py"])))
        self.assertTrue(requires_restart(FileChanges(modified=["a/tasks.py"])))
        self.assertTrue(requires_restart(FileChanges(modified=["settings.json"])))
        self.assertFalse(requires_restart(FileChanges(modified=["a/views.py"])))


if __name__ == "__main__":
    unittest.main()
