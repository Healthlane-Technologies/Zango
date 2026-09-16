"""The run hand-off needs a link, not just credentials.

Two things this pins down:

* The front door is read from `app_routes`, never assumed. Real apps differ —
  Tender361 mounts its `app` module at `^` (site root) while the skill's
  worked example uses `^app/`, so a hardcoded path is wrong for one of them.
* An app with no domain row is genuinely unreachable (tenants resolve strictly
  by hostname), so the API must return an empty URL rather than fabricate one.
"""

import unittest

from zango.apps.agent_mode.context import app_access, app_front_door


class _Domain:
    def __init__(self, domain, is_primary=False):
        self.domain = domain
        self.is_primary = is_primary


class _Domains:
    def __init__(self, items):
        self._items = items

    def all(self):
        return list(self._items)


class _Tenant:
    def __init__(self, name, domains):
        self.name = name
        self.domains = _Domains(domains)


class _Request:
    def __init__(self, host, secure=False):
        self._host = host
        self._secure = secure

    def get_host(self):
        return self._host

    def is_secure(self):
        return self._secure


class FrontDoorTests(unittest.TestCase):
    """The UI lives at /app/. The path is split across settings.json (which
    mounts the module) and the module's own urls.py (which puts the view under
    it), so reading only the mount point gets it wrong."""

    def test_module_mounted_at_site_root(self):
        """Tender361, TaskApp52, TestApp591: mount ^, urls.py ^app/."""
        settings = {
            "app_routes": [
                {"re_path": "^", "module": "app", "url": "urls"},
                {"re_path": "^tenders/", "module": "tenders", "url": "urls"},
            ]
        }
        self.assertEqual(app_front_door(settings), "/app/")

    def test_module_mounted_at_app(self):
        """PatientNavigator, and the skill's own template: mount ^app/."""
        settings = {
            "app_routes": [
                {"re_path": "^institutions/", "module": "institutions", "url": "urls"},
                {"re_path": "^app/", "module": "app", "url": "urls"},
            ]
        }
        # Chosen by module name, not by position — and not doubled to /app/app/.
        self.assertEqual(app_front_door(settings), "/app/")

    def test_custom_mount_keeps_the_app_suffix(self):
        settings = {"app_routes": [{"re_path": "^portal/", "module": "app"}]}
        self.assertEqual(app_front_door(settings), "/portal/app/")

    def test_no_routes_still_points_at_app(self):
        self.assertEqual(app_front_door({}), "/app/")
        self.assertEqual(app_front_door({"app_routes": []}), "/app/")
        self.assertEqual(app_front_door(None), "/app/")

    def test_regex_anchors_are_stripped(self):
        self.assertEqual(
            app_front_door({"app_routes": [{"re_path": "^app/$", "module": "app"}]}),
            "/app/",
        )

    def test_junk_entries_do_not_raise(self):
        self.assertEqual(app_front_door({"app_routes": ["nonsense", None]}), "/app/")

    def test_every_real_workspace_layout_yields_app(self):
        """Both layouts seen in this install must converge."""
        for mount in ("^", "^app/", "^app/$", ""):
            self.assertEqual(
                app_front_door({"app_routes": [{"re_path": mount, "module": "app"}]}),
                "/app/",
                f"mount {mount!r} did not resolve to /app/",
            )


class AppAccessTests(unittest.TestCase):
    SETTINGS = {"app_routes": [{"re_path": "^", "module": "app", "url": "urls"}]}

    def test_dev_link_carries_scheme_and_port_from_the_request(self):
        """Without the port the link is dead on a dev server."""
        tenant = _Tenant("Tender361", [_Domain("tender361.zango.com", True)])
        access = app_access(
            tenant,
            request=_Request("localhost:8000"),
            app_settings=self.SETTINGS,
        )
        self.assertEqual(access["url"], "http://tender361.zango.com:8000/app/")
        self.assertEqual(access["domain"], "tender361.zango.com")

    def test_production_link_is_https_without_a_port(self):
        tenant = _Tenant("Tender361", [_Domain("tender361.zango.com", True)])
        access = app_access(
            tenant,
            request=_Request("panel.zango.com", secure=True),
            app_settings=self.SETTINGS,
        )
        self.assertEqual(access["url"], "https://tender361.zango.com/app/")

    def test_primary_domain_wins_over_order(self):
        tenant = _Tenant(
            "X",
            [_Domain("alias.zango.com"), _Domain("real.zango.com", True)],
        )
        self.assertEqual(
            app_access(tenant, app_settings=self.SETTINGS)["domain"],
            "real.zango.com",
        )

    def test_first_domain_used_when_none_is_primary(self):
        tenant = _Tenant("X", [_Domain("only.zango.com")])
        self.assertEqual(
            app_access(tenant, app_settings=self.SETTINGS)["domain"],
            "only.zango.com",
        )

    def test_app_without_a_domain_has_no_url(self):
        """Many apps in this install have no domain row at all."""
        access = app_access(_Tenant("TestApp1", []), app_settings=self.SETTINGS)
        self.assertEqual(access["url"], "")
        self.assertEqual(access["domain"], "")

    def test_prefix_path_is_included(self):
        tenant = _Tenant("X", [_Domain("x.zango.com", True)])
        access = app_access(
            tenant,
            request=_Request("localhost:8000"),
            app_settings={"app_routes": [{"re_path": "^app/", "module": "app"}]},
        )
        self.assertEqual(access["url"], "http://x.zango.com:8000/app/")

    def test_broken_request_object_does_not_raise(self):
        class Bad:
            def get_host(self):
                raise RuntimeError("boom")

            def is_secure(self):
                raise RuntimeError("boom")

        tenant = _Tenant("X", [_Domain("x.zango.com", True)])
        access = app_access(tenant, request=Bad(), app_settings=self.SETTINGS)
        self.assertEqual(access["url"], "https://x.zango.com/app/")


class DetailViewWiringTests(unittest.TestCase):
    def test_detail_view_returns_app_access(self):
        import inspect

        from zango.api.platform.agent_mode.v1 import views

        source = inspect.getsource(views.AgentRunDetailView)
        self.assertIn('data["app_access"]', source)
        self.assertIn("app_access(tenant, request=request)", source)
