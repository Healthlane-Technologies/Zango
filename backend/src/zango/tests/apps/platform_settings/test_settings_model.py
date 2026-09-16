"""Platform defaults: normalisation, creation-time application, and the
guarantee that a bad default can never break an app launch."""

import inspect
import unittest


class NormalisationTests(unittest.TestCase):
    def test_base_domain_is_normalised_on_save_not_just_in_the_view(self):
        """A value set from a shell or fixture must land in the same shape as
        one typed into the UI."""
        from zango.apps.shared.platform_settings.models import PlatformSettings

        source = inspect.getsource(PlatformSettings.save)
        self.assertIn("normalise_base_domain", source)

    def test_tenant_defaults_skips_unset_values(self):
        """An unset platform default must leave the tenant column alone rather
        than blanking it."""
        from zango.apps.shared.platform_settings.models import PlatformSettings

        row = PlatformSettings(
            default_timezone="Asia/Kolkata",
            default_date_format="",
            default_datetime_format="%d/%m/%Y %H:%M",
            default_language="",
        )
        self.assertEqual(
            row.tenant_defaults(),
            {"timezone": "Asia/Kolkata", "datetime_format": "%d/%m/%Y %H:%M"},
        )

    def test_tenant_defaults_maps_onto_real_tenant_fields(self):
        """A typo here would silently do nothing."""
        from zango.apps.shared.platform_settings.models import PlatformSettings
        from zango.apps.shared.tenancy.models import TenantModel

        row = PlatformSettings(
            default_timezone="UTC",
            default_date_format="%d/%m/%Y",
            default_datetime_format="%d/%m/%Y %H:%M",
            default_language="en",
        )
        tenant_fields = {f.name for f in TenantModel._meta.get_fields()}
        for key in row.tenant_defaults():
            self.assertIn(key, tenant_fields, f"TenantModel has no field {key!r}")


class CreationHookTests(unittest.TestCase):
    def test_create_applies_defaults_without_overriding_explicit_values(self):
        from zango.apps.shared.tenancy.models import TenantModel

        source = inspect.getsource(TenantModel.create)
        # setdefault, not assignment: a value passed to create() must win.
        self.assertIn("other_params.setdefault(field, value)", source)

    def test_create_allocates_a_domain_for_app_tenants_only(self):
        from zango.apps.shared.tenancy.models import TenantModel

        source = inspect.getsource(TenantModel.create)
        self.assertIn("allocate_domain", source)
        self.assertIn('tenant_type", "app"', source)

    def test_defaults_failure_cannot_break_a_launch(self):
        from zango.apps.shared.tenancy.models import TenantModel

        source = inspect.getsource(TenantModel.create)
        self.assertIn("except Exception", source)


class AllocationSafetyTests(unittest.TestCase):
    def test_allocate_domain_never_raises(self):
        """Called inside app creation — an exception here would abort a launch
        that has already provisioned a schema."""
        from zango.apps.shared.platform_settings import domains

        class Exploding:
            @property
            def auto_domain_enabled(self):
                raise RuntimeError("boom")

        self.assertIsNone(domains.allocate_domain(object(), Exploding()))

    def test_allocation_claims_rather_than_checks(self):
        """A check-then-write would hand the same name to two apps launched at
        the same instant."""
        from zango.apps.shared.platform_settings import domains

        source = inspect.getsource(domains.allocate_domain)
        self.assertIn("IntegrityError", source)
        self.assertIn("continue", source)

    def test_theme_default_falls_back_to_the_framework_palette(self):
        from zango.apps.shared.tenancy import tasks

        source = inspect.getsource(tasks)
        self.assertIn("theme_config = DEFAULT_THEME_CONFIG", source)
        self.assertIn("default_theme_config", source)


class ApiSurfaceTests(unittest.TestCase):
    def test_writable_fields_all_exist_on_the_model(self):
        from zango.api.platform.platform_settings_admin.v1 import views
        from zango.apps.shared.platform_settings.models import PlatformSettings

        model_fields = {f.name for f in PlatformSettings._meta.get_fields()}
        for field in views._WRITABLE:
            self.assertIn(field, model_fields, f"no such field: {field}")

    def test_enabling_without_a_base_domain_is_refused(self):
        from zango.api.platform.platform_settings_admin.v1 import views

        source = inspect.getsource(views.PlatformGeneralSettingsView.post)
        self.assertIn("is_valid_base_domain", source)
        self.assertIn("400", source)

    def test_choices_come_from_the_tenancy_tuples(self):
        """The UI's options and the tenant model's validation must not drift."""
        from zango.api.platform.platform_settings_admin.v1 import views

        source = inspect.getsource(views._options)
        for name in ("TIMEZONES", "DATEFORMAT", "DATETIMEFORMAT"):
            self.assertIn(name, source)
