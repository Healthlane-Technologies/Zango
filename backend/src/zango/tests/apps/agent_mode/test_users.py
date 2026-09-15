"""Test-user declaration.

An app with correct code, correct policies and no users is not a working
app — the interactive skill's final step exists for a reason.
"""

import json
import os
import shutil
import string
import tempfile
import unittest

from zango.apps.agent_mode.users import (
    MAX_USERS,
    declared_users,
    generate_password,
)


class DeclaredUsersTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ws-")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, payload):
        with open(os.path.join(self.root, "users.json"), "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

    def test_absent_file_is_empty(self):
        self.assertEqual(declared_users(self.root), [])

    def test_object_form(self):
        self._write(
            {
                "users": [
                    {"name": "Task Admin", "email": "a@demo.test", "role": "TaskAdmin"},
                ]
            }
        )
        users = declared_users(self.root)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["email"], "a@demo.test")
        self.assertEqual(users[0]["role"], "TaskAdmin")

    def test_name_defaults_from_email(self):
        self._write({"users": [{"email": "member@demo.test", "role": "R"}]})
        self.assertEqual(declared_users(self.root)[0]["name"], "member")

    def test_role_name_alias_accepted(self):
        self._write({"users": [{"email": "x@demo.test", "role_name": "R"}]})
        self.assertEqual(declared_users(self.root)[0]["role"], "R")

    def test_entries_without_email_or_role_are_dropped(self):
        self._write(
            {
                "users": [
                    {"email": "ok@demo.test", "role": "R"},
                    {"email": "", "role": "R"},
                    {"email": "norole@demo.test"},
                ]
            }
        )
        self.assertEqual(len(declared_users(self.root)), 1)

    def test_capped(self):
        self._write(
            {
                "users": [
                    {"email": f"u{i}@demo.test", "role": "R"}
                    for i in range(MAX_USERS + 15)
                ]
            }
        )
        self.assertEqual(len(declared_users(self.root)), MAX_USERS)

    def test_malformed_file_does_not_raise(self):
        with open(os.path.join(self.root, "users.json"), "w") as fh:
            fh.write("{nope")
        self.assertEqual(declared_users(self.root), [])


class PasswordTests(unittest.TestCase):
    def test_shape_and_uniqueness(self):
        pwds = {generate_password() for _ in range(50)}
        self.assertEqual(len(pwds), 50, "generated passwords must not repeat")
        for pwd in pwds:
            self.assertGreaterEqual(len(pwd), 12)
            self.assertTrue(any(c.isupper() for c in pwd))
            self.assertTrue(any(c.islower() for c in pwd))
            self.assertTrue(any(c.isdigit() for c in pwd))
            self.assertTrue(any(c in string.punctuation for c in pwd))


if __name__ == "__main__":
    unittest.main()
