from zango.test.cases import ZangoAppBaseTestCase
from django.test import override_settings
from zango.apps.appauth.models import UserRoleModel
from zango.apps.permissions.models import PolicyModel
from django.db import connection
from zango.apps.dynamic_models.workspace.base import Workspace


@override_settings(ROOT_URLCONF="src.test_project.test_project.url_tenants")
class ZangoModulesTest(ZangoAppBaseTestCase):

    def test_role_policy_mapping(self):
        # passing same module name in this class again will throw error.
        self.setUpAppAndModule("policy_tests", "test_role_policy_mapping")
        with connection.cursor() as c:
            ws = Workspace(self.tenant, as_systemuser=True)
            ws.ready()
            ws.sync_policies()
        
        expected_role_names = ["test_role_1", "test_role_2"]
        expected_policy_name = "CustomerGetViewAccess"

        for role_name in expected_role_names:
            role = UserRoleModel.objects.filter(name=role_name).first()
            self.assertIsNotNone(role, f"Role '{role_name}' does not exist")
            
            policies = role.policies.all()
            
            self.assertTrue(
                policies.filter(name=expected_policy_name).exists(),
                f"Role '{role_name}' does not have expected policy '{expected_policy_name}'"
            )

        policy = PolicyModel.objects.filter(name=expected_policy_name).first()
        self.assertIsNotNone(policy, f"Policy '{expected_policy_name}' does not exist")
        

        roles = policy.role_policies.all()
        
        for role_name in expected_role_names:
            self.assertTrue(
                roles.filter(name=role_name).exists(),
                f"Policy '{expected_policy_name}' is not associated with role '{role_name}'"
            )