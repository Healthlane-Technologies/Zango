from zelthy3.backend.apps.tenants.dynamic_models.workspace.base import Workspace
from django_tenants.utils import get_tenant_model, get_tenant_domain_model, get_public_schema_name
from django.db import connection, models
from django.conf import settings
from zelthy3.backend.apps.tenants.dynamic_models.fields import ZForeignKey
from zelthy3.backend.apps.tenants.dynamic_models.models import DynamicModelBase
from django.core.exceptions import FieldError
from workspaces.Tenant3.null_fk.models import Comment, Forum, Item, NPost, PropertyValue, SystemDetails, SystemInfo
import unittest
import django
import subprocess
from django.db.models import Q
from django.test import TestCase
from django.core.management import call_command
from django.conf import settings



class TenantTestCase(TestCase):
    tenant = None
    domain = None

    @classmethod
    def setup_tenant(cls, tenant):
        """
        Add any additional setting to the tenant before it get saved. This is required if you have
        required fields.
        :param tenant:
        :return:
        """
        pass

    @classmethod
    def setup_domain(cls, domain):
        """
        Add any additional setting to the domain before it get saved. This is required if you have
        required fields.
        :param domain:
        :return:
        """
        pass

    @classmethod
    def setUpClass(cls):
        cls.sync_shared()
        # cls.add_allowed_test_domain()
        cls.tenant = get_tenant_model()(schema_name=cls.get_test_schema_name(), name="Tenant3", app_type="tenant")
        cls.setup_tenant(cls.tenant)
        cls.tenant.save()
        cls.zoperations()
        # Set up domain
        tenant_domain = cls.get_test_tenant_domain()
        cls.domain = get_tenant_domain_model()(tenant=cls.tenant, domain=tenant_domain)
        cls.setup_domain(cls.domain)
        cls.domain.save()
        print("cls.tenant", cls.tenant)
        connection.set_tenant(cls.tenant)

    @classmethod
    def tearDownClass(cls):
        pass
        # connection.set_schema_to_public()
        # cls.domain.delete()
        # cls.tenant.delete(force_drop=True)
        # cls.remove_allowed_test_domain()

    @classmethod
    def get_verbosity(cls):
        return 0

    # @classmethod
    # def add_allowed_test_domain(cls):
    #     tenant_domain = cls.get_test_tenant_domain()

    #     # ALLOWED_HOSTS is a special setting of Django setup_test_environment so we can't modify it with helpers
    #     if tenant_domain not in settings.ALLOWED_HOSTS:
    #         settings.ALLOWED_HOSTS += [tenant_domain]

    # @classmethod
    # def remove_allowed_test_domain(cls):
    #     tenant_domain = cls.get_test_tenant_domain()

    #     if tenant_domain in settings.ALLOWED_HOSTS:
    #         settings.ALLOWED_HOSTS.remove(tenant_domain)

    @classmethod
    def sync_shared(cls):
        call_command('migrate_schemas',
                     schema_name=get_public_schema_name(),
                     interactive=False,
                     verbosity=0)
    
    @classmethod
    def zoperations(cls):
        settings.TEST_MIGRATION_RUNNING = True
        tenant = "Tenant3"
        command1 = f"python manage.py zmakemigrations {tenant} --test"
        subprocess.run(command1, shell=True)
        # from django.apps import apps
        # print(apps.get_models())
        db_name = settings.DATABASES['default']['NAME']
        print(db_name)
        # settings.DATABASES['default']['NAME'] = "test_" + db_name      
        # print(settings.DATABASES['default'])  
        command2 = f"python manage.py zmigrate {tenant} --test"
        # settings.DATABASES['default']['NAME'] = db_name
        subprocess.run(command2, shell=True)
        

    @classmethod
    def get_test_tenant_domain(cls):
        return 'localhost'

    @classmethod
    def get_test_schema_name(cls):
        return 'Tenant3'

class TestForeignKey(TenantTestCase):

    def test_null_fk(self):
        d = SystemDetails.objects.create(details="First details")
        s = SystemInfo.objects.create(system_name="First forum", system_details=d)
        f = Forum.objects.create(system_info=s, forum_name="First forum")
        p = NPost.objects.create(forum=f, title="First Post")
        c1 = Comment.objects.create(post=p, comment_text="My first comment")
        c2 = Comment.objects.create(comment_text="My second comment")
        print(d, s, f, p, c1, c2)

        # Starting from comment, make sure that a .select_related(...) with a specified
        # set of fields will properly LEFT JOIN multiple levels of NULLs (and the things
        # that come after the NULLs, or else data that should exist won't). Regression
        # test for #7369.
        c = Comment.objects.select_related().get(id=c1.id)
        print(c)
        print(c.post)
        print(p)
        
        self.assertEqual(c.post, p)
        print(c.post == p)
        self.assertIsNone(Comment.objects.select_related().get(id=c2.id).post)
        print("here")
        self.assertQuerySetEqual(
            Comment.objects.select_related("post__forum__system_info").all(),
            [
                (c1.id, "My first comment", "<Post: First Post>"),
                (c2.id, "My second comment", "None"),
            ],
            transform=lambda c: (c.id, c.comment_text, repr(c.post)),
        )
        print("here1")

        # Regression test for #7530, #7716.
        self.assertIsNone(
            Comment.objects.select_related("post").filter(post__isnull=True)[0].post
        )
        print("her2")

        # self.assertQuerySetEqual(
        #     Comment.objects.select_related("post__forum__system_info__system_details"),
        #     [
        #         (c1.id, "My first comment", "<Post: First Post>"),
        #         (c2.id, "My second comment", "None"),
        #     ],
        #     transform=lambda c: (c.id, c.comment_text, repr(c.post)),
        # )
        print("her3")

    def test_combine_isnull(self):
        item = Item.objects.create(title="Some Item")
        pv = PropertyValue.objects.create(label="Some Value")
        item.props.create(key="a", value=pv)
        item.props.create(key="b")  # value=NULL
        q1 = Q(props__key="a", props__value=pv)
        q2 = Q(props__key="b", props__value__isnull=True)

        # Each of these individually should return the item.
        self.assertEqual(Item.objects.get(q1), item)
        self.assertEqual(Item.objects.get(q2), item)
        print("here5")

        # Logically, qs1 and qs2, and qs3 and qs4 should be the same.
        qs1 = Item.objects.filter(q1) & Item.objects.filter(q2)
        qs2 = Item.objects.filter(q2) & Item.objects.filter(q1)
        qs3 = Item.objects.filter(q1) | Item.objects.filter(q2)
        qs4 = Item.objects.filter(q2) | Item.objects.filter(q1)

        # Regression test for #15823.
        self.assertEqual(list(qs1), list(qs2))
        self.assertEqual(list(qs3), list(qs4))
        print("here6")