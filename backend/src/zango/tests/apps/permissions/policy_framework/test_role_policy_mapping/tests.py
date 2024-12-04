import os

from django_tenants.utils import schema_context
from zango.test.cases import ZangoAppBaseTestCase
from django.test import override_settings
from zango.apps.appauth.models import UserRoleModel
from zango.apps.permissions.models import PolicyModel
from django.db import connection
from zango.apps.dynamic_models.workspace.base import Workspace


@override_settings(ROOT_URLCONF="src.test_project.test_project.url_tenants")
class RolePolicyMappingTest(ZangoAppBaseTestCase):
    initialize_workspace = True

    @classmethod
    def get_test_module_path(self):
        return os.path.join(
            "apps/permissions/policy_framework/test_role_policy_mapping"
        )

    @classmethod
    def sync_policies(self):
        with schema_context(self.tenant.schema_name):
            ws = Workspace(self.tenant, as_systemuser=True)
            ws.ready()
            ws.sync_policies()

    def test_multi_role_with_one_policy_mapping(self):

        expected_role_names = ["test_role_1", "test_role_2"]
        expected_policy_name = "CustomerGetViewAccess"
        UserRoleModel.objects.create(name="test_role_1")
        UserRoleModel.objects.create(name="test_role_2")
        UserRoleModel.objects.create(name="dummy_role_1")

        self.sync_policies()

        for role_name in expected_role_names:
            role = UserRoleModel.objects.filter(name=role_name).first()
            self.assertIsNotNone(role, f"Role '{role_name}' does not exist")

            policies = role.policies.all()

            self.assertTrue(
                policies.filter(name=expected_policy_name).exists(),
                f"Role '{role_name}' does not have expected policy '{expected_policy_name}'",
            )

        policy = PolicyModel.objects.filter(name=expected_policy_name).first()
        self.assertIsNotNone(policy, f"Policy '{expected_policy_name}' does not exist")

        roles = policy.role_policies.all()

        for role_name in expected_role_names:
            self.assertTrue(
                roles.filter(name=role_name).exists(),
                f"Policy '{expected_policy_name}' is not associated with role '{role_name}'",
            )

    def test_one_role_with_multi_policy_mapping(self):
        expected_role_name = "dummy_role_1"
        expected_policy_names = ["RetailersGetViewAccess", "DummyGetViewAccess"]
        with schema_context(self.tenant.schema_name):
            UserRoleModel.objects.create(name="test_role_1")
            UserRoleModel.objects.create(name="test_role_2")
            UserRoleModel.objects.create(name=expected_role_name)

        self.sync_policies()

        role = UserRoleModel.objects.filter(name=expected_role_name).first()
        self.assertIsNotNone(role, f"Role '{expected_role_name}' does not exist")

        policies = role.policies.all()

        for policy_name in expected_policy_names:
            self.assertTrue(
                policies.filter(name=policy_name).exists(),
                f"Role '{expected_role_name}' does not have expected policy '{policy_name}'",
            )

        for policy_name in expected_policy_names:
            policy = PolicyModel.objects.filter(name=policy_name).first()
            self.assertIsNotNone(policy, f"Policy '{policy_name}' does not exist")
            roles = policy.role_policies.all()

            self.assertTrue(
                roles.filter(name=expected_role_name).exists(),
                f"Policy '{policy_name}' is not associated with role '{expected_role_name}'",
            )
