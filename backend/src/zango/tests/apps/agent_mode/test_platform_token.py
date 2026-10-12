"""The ?token= a platform user is given for package configuration.

Regression: it was signed with ``request.user.id`` (the Django auth user)
but read back as a platform-user id. The two only coincide for the first
superadmin, so AppBuilder rejected every other account — including the
service account an App Studio build signs in with, which left built apps
with no menus and none of their tests run.
"""

import unittest

from types import SimpleNamespace
from unittest import mock

from django.core import signing

from zango.apps.dynamic_models import permissions


class PlatformUserTokenTests(unittest.TestCase):
    def test_the_token_carries_the_platform_users_id_not_the_auth_users(self):
        request = SimpleNamespace(user=SimpleNamespace(id=19, platform_user=SimpleNamespace(id=17)))
        self.assertEqual(signing.loads(permissions.platform_user_token(request)), 17)

    def test_what_is_minted_is_what_is_looked_up(self):
        request = SimpleNamespace(user=SimpleNamespace(id=19, platform_user=SimpleNamespace(id=17)))
        token = permissions.platform_user_token(request)
        with mock.patch.object(permissions.PlatformUserModel, "objects") as objects:
            permissions.get_platform_user(SimpleNamespace(GET={"token": token}))
        objects.get.assert_called_once_with(id=17)


if __name__ == "__main__":
    unittest.main()
