import os
import json
import base64
from cryptography.fernet import Fernet
from django_tenants.utils import schema_context
from zango.test.cases import ZangoAppBaseTestCase
from django.test import override_settings
from django.db import connection
from zango.apps.secrets.models import SecretsModel
from zango.core.utils import get_app_secret
from django.conf import settings


@override_settings(ROOT_URLCONF="src.test_project.test_project.url_tenants")
class ZangoAppSecretTest(ZangoAppBaseTestCase):
    initialize_workspace = True

    @classmethod
    def setUpClass(cls):
        # Generate a test encryption key
        key = base64.urlsafe_b64encode(Fernet.generate_key()[:32])
        settings.FIELD_ENCRYPTION_KEY = key
        super().setUpClass()

    def setUp(self):
        super().setUp()
        # Ensure the encryption key is set for each test
        if not hasattr(settings, 'FIELD_ENCRYPTION_KEY') or not settings.FIELD_ENCRYPTION_KEY:
            key = base64.urlsafe_b64encode(Fernet.generate_key()[:32])
            settings.FIELD_ENCRYPTION_KEY = key

    @classmethod
    def get_test_module_path(self):
        return os.path.join(
            "apps/secrets/test_secrets"
        )
    
    def test_secret_creation(self):
        SecretsModel.objects.create(key="Key1", value="Value1")
    
    def test_secret_retrieval(self):
        sec = SecretsModel.objects.create(key="Key3", value="Value3")

        utils_value = get_app_secret("Key3")
        sec = SecretsModel.objects.get(key="Key3")
        value = sec.get_unencrypted_val()

        self.assertEqual(utils_value, value)
    
    def test_inactive_exception(self):
        sec = SecretsModel.objects.create(key="Key2", value="Value2")
        sec.is_active = False
        sec.save()
        with self.assertRaises(ValueError):
            get_app_secret(key="Key2")
    
        with self.assertRaises(ValueError):
            get_app_secret(id=sec.id)
    
    def test_secret_update(self):
        sec = SecretsModel.objects.create(key="Key4", value="Value4")
        sec.value = "Value5"
        sec.save()
        utils_value = get_app_secret("Key4")
        self.assertEqual(utils_value, "Value5")

        sec.key = "Key6"
        sec.save()
        utils_value = get_app_secret("Key6")
        self.assertEqual(utils_value, "Value5")
    
    def test_secret_delete(self):
        sec = SecretsModel.objects.create(key="Key5", value="Value5")
        sec.delete()
        with self.assertRaises(ValueError):
            get_app_secret("Key5")
        
        
