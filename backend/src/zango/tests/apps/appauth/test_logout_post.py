"""appbuilder's logout page (/app/logout) signs out with POST /logout and reads JSON."""

import json

from unittest import mock

from django.test import RequestFactory, SimpleTestCase

from zango.apps.appauth import views


class LogoutPostTests(SimpleTestCase):
    def test_post_signs_out_and_answers_json(self):
        request = RequestFactory().post("/logout/")
        with mock.patch.object(views, "logout") as logout:
            response = views.AppLogoutView().post(request)
        logout.assert_called_once_with(request)
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertTrue(body["success"])
        self.assertEqual(body["response"]["message"], "Successfully logged out")
