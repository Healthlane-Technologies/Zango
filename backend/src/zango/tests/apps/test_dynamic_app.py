from zango.test.cases import ZangoAppBaseTestCase
from zango.apps.shared.tenancy.tasks import initialize_workspace


class DynamicZangoAppTest(ZangoAppBaseTestCase):
    def test_dynamic_app_creation(self):
        res = initialize_workspace(self.tenant.uuid)
        self.assertDictEqual(res, {"result" : "success"})
        self.clean_workspaces()
