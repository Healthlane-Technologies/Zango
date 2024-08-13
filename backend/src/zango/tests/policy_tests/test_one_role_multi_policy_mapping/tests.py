from zango.test.cases import ZangoAppBaseTestCase
from django.test import override_settings
from zango.apps.appauth.models import UserRoleModel
from zango.apps.permissions.models import PolicyModel
from django.db import connection
from zango.apps.dynamic_models.workspace.base import Workspace


@override_settings(ROOT_URLCONF="src.test_project.test_project.url_tenants")
class ZangoModulesTest(ZangoAppBaseTestCase):

    def test_one_role_with_multi_policy_mapping(self):
        # passing same module name in this class again will throw error.
        self.setUpAppAndModule("policy_tests", "test_one_role_multi_policy_mapping")
        with connection.cursor() as c:
            ws = Workspace(self.tenant, as_systemuser=True)
            ws.ready()
            ws.sync_policies()
        
        expected_role_name = "test_role_1"
        expected_policy_names = ["CustomerGetViewAccess", "DummyGetViewAccess"]

        role = UserRoleModel.objects.filter(name=expected_role_name).first()
        self.assertIsNotNone(role, f"Role '{expected_role_name}' does not exist")
        
        policies = role.policies.all()

        for policy_name in expected_policy_names:
            self.assertTrue(
                policies.filter(name=policy_name).exists(),
                f"Role '{expected_role_name}' does not have expected policy '{policy_name}'"
            )

        for policy_name in expected_policy_names:
            policy = PolicyModel.objects.filter(name=policy_name).first()
            self.assertIsNotNone(policy, f"Policy '{policy_name}' does not exist")
            roles = policy.role_policies.all()

            self.assertTrue(
                roles.filter(name=expected_role_name).exists(),
                f"Policy '{policy_name}' is not associated with role '{expected_role_name}'"
            )