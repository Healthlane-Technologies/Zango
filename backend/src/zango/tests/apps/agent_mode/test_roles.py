"""Role reconciliation.

`Workspace.sync_policies_with_roles` silently skips policy roles that do not
exist, so a missing role produces views nobody can reach with no error. These
tests cover the collection side (pure filesystem); creation is exercised
against the live schema separately.
"""

import json
import os
import shutil
import tempfile
import unittest

from zango.apps.agent_mode.roles import (
    RESERVED_ROLES,
    declared_roles,
    referenced_roles,
)


def write_json(root, rel, payload):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


class DeclaredRolesTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ws-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_absent_file_is_empty(self):
        self.assertEqual(declared_roles(self.root), [])

    def test_object_form(self):
        write_json(
            self.root,
            "roles.json",
            {"roles": [{"name": "Admin", "description": "x"}, {"name": "Approver"}]},
        )
        self.assertEqual(declared_roles(self.root), ["Admin", "Approver"])

    def test_plain_list_form(self):
        write_json(self.root, "roles.json", ["Admin", "Staff"])
        self.assertEqual(declared_roles(self.root), ["Admin", "Staff"])

    def test_malformed_file_does_not_raise(self):
        with open(os.path.join(self.root, "roles.json"), "w") as fh:
            fh.write("{not json")
        self.assertEqual(declared_roles(self.root), [])


class ReferencedRolesTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ws-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_collects_across_modules_and_dedupes(self):
        write_json(
            self.root,
            "backend/expenses/policies.json",
            {
                "policies": [
                    {"name": "p1", "roles": ["Admin", "Approver"]},
                    {"name": "p2", "roles": ["Admin"]},
                ]
            },
        )
        write_json(
            self.root,
            "backend/audit/policies.json",
            {
                "policies": [
                    {"name": "p3", "roles": ["Auditor"]},
                ]
            },
        )
        self.assertEqual(referenced_roles(self.root), ["Admin", "Approver", "Auditor"])

    def test_policy_without_roles_is_fine(self):
        write_json(self.root, "backend/a/policies.json", {"policies": [{"name": "p"}]})
        self.assertEqual(referenced_roles(self.root), [])

    def test_ignores_vendored_noise(self):
        write_json(
            self.root,
            "node_modules/x/policies.json",
            {"policies": [{"name": "p", "roles": ["ShouldNotAppear"]}]},
        )
        self.assertEqual(referenced_roles(self.root), [])

    def test_malformed_policies_file_is_skipped(self):
        os.makedirs(os.path.join(self.root, "backend/bad"), exist_ok=True)
        with open(os.path.join(self.root, "backend/bad/policies.json"), "w") as fh:
            fh.write("[[[")
        write_json(
            self.root,
            "backend/ok/policies.json",
            {"policies": [{"name": "p", "roles": ["Admin"]}]},
        )
        self.assertEqual(referenced_roles(self.root), ["Admin"])

    def test_reserved_roles_are_known(self):
        self.assertIn("SystemUsers", RESERVED_ROLES)
        self.assertIn("AnonymousUsers", RESERVED_ROLES)


if __name__ == "__main__":
    unittest.main()
