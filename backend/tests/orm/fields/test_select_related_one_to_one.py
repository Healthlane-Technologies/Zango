import unittest
from zelthy3.backend.apps.tenants.dynamic_models.workspace.base import Workspace
from django_tenants.utils import get_tenant_model
from django.db import connection
from django.core.exceptions import FieldError
from workspaces.Tenant3.one_to_one.models import (
    Image,
    Parent1,
    Parent2,
    Product,
    StatDetails,
    OUser,
    UserProfile,
    UserStat,
    UserStatResult,
)

class TestSelectRelatedOneToOne(unittest.TestCase):

    def setUp(self) -> None:
        tenant_model = get_tenant_model()
        env = tenant_model.objects.get(name="Tenant3")
        connection.set_tenant(env)
        ws = Workspace(connection.tenant)
        ws.ready()
        with connection.cursor() as c:
            user = OUser.objects.create(username="test")
            UserProfile.objects.create(user=user, state="KS", city="Lawrence")
            results = UserStatResult.objects.create(results="first results")
            userstat = UserStat.objects.create(user=user, posts=150, results=results)
            StatDetails.objects.create(base_stats=userstat, comments=259)

            user2 = OUser.objects.create(username="bob")
            results2 = UserStatResult.objects.create(results="moar results")
            # advstat = AdvancedUserStat.objects.create(
            #     user=user2, posts=200, karma=5, results=results2
            # )
            # StatDetails.objects.create(base_stats=advstat, comments=250)
            # p1 = Parent1(name1="Only Parent1")
            # p1.save()
            # c1 = Child1(name1="Child1 Parent1", name2="Child1 Parent2", value=1)
            # c1.save()
            # p2 = Parent2(name2="Child2 Parent2")
            # p2.save()
            # c2 = Child2(name1="Child2 Parent1", parent2=p2, value=2)
            # c2.save()
    
    def test_basic(self):
        with connection.cursor() as c:
            u = OUser.objects.select_related("userprofile").get(username="test")
            self.assertEqual(u.userprofile.state, "KS")

    def test_follow_next_level(self):
        with connection.cursor() as c:
            u = OUser.objects.select_related("userstat__results").get(username="test")
            self.assertEqual(u.userstat.posts, 150)
            self.assertEqual(u.userstat.results.results, "first results")

    def test_follow_two(self):
        with connection.cursor() as c:
            u = OUser.objects.select_related("userprofile", "userstat").get(
                username="test"
            )
            self.assertEqual(u.userprofile.state, "KS")
            self.assertEqual(u.userstat.posts, 150)

    def test_follow_two_next_level(self):
        with connection.cursor() as c:
            u = OUser.objects.select_related(
                "userstat__results", "userstat__statdetails"
            ).get(username="test")
            self.assertEqual(u.userstat.results.results, "first results")
            self.assertEqual(u.userstat.statdetails.comments, 259)

    def test_forward_and_back(self):
        with connection.cursor() as c:
            stat = UserStat.objects.select_related("user__userprofile").get(
                user__username="test"
            )
            self.assertEqual(stat.user.userprofile.state, "KS")
            self.assertEqual(stat.user.userstat.posts, 150)

    def test_back_and_forward(self):
        with connection.cursor() as c:
            u = OUser.objects.select_related("userstat").get(username="test")
            self.assertEqual(u.userstat.user.username, "test")

    def test_not_followed_by_default(self):
        with connection.cursor() as c:
            u = OUser.objects.select_related().get(username="test")
            self.assertEqual(u.userstat.posts, 150)


    def test_follow_inheritance(self):
        with connection.cursor() as c:
            stat = UserStat.objects.select_related("user", "advanceduserstat").get(
                posts=200
            )
            self.assertEqual(stat.advanceduserstat.posts, 200)
            self.assertEqual(stat.user.username, "bob")
            self.assertEqual(stat.advanceduserstat.user.username, "bob")

    def test_nullable_relation(self):
        with connection.cursor() as c:
            im = Image.objects.create(name="imag1")
            p1 = Product.objects.create(name="Django Plushie", image=im)
            p2 = Product.objects.create(name="Talking Django Plushie")

            result = sorted(
                Product.objects.select_related("image"), key=lambda x: x.name
            )
            self.assertEqual(
                [p.name for p in result], ["Django Plushie", "Talking Django Plushie"]
            )

            self.assertEqual(p1.image, im)
            # Check for ticket #13839
            self.assertIsNone(p2.image)

    def test_missing_reverse(self):
        """
        Ticket #13839: select_related() should NOT cache None
        for missing objects on a reverse 1-1 relation.
        """
        with connection.cursor() as c:
            user = OUser.objects.select_related("userprofile").get(username="bob")
            with self.assertRaises(UserProfile.DoesNotExist):
                user.userprofile

    def test_nullable_missing_reverse(self):
        """
        Ticket #13839: select_related() should NOT cache None
        for missing objects on a reverse 0-1 relation.
        """
        

        with connection.cursor() as c:
            Image.objects.create(name="imag1")
            image = Image.objects.select_related("product").get()
            with self.assertRaises(Product.DoesNotExist):
                image.product



    def test_multiple_subclass(self):
        with connection.cursor() as c:
            p = Parent1.objects.select_related("child1").get(name1="Child1 Parent1")
            self.assertEqual(p.child1.name2, "Child1 Parent2")

    def test_onetoone_with_subclass(self):
        with connection.cursor() as c:
            p = Parent2.objects.select_related("child2").get(name2="Child2 Parent2")
            self.assertEqual(p.child2.name1, "Child2 Parent1")

    # def test_self_relation(self):
        
    #     with connection.cursor() as c:
    #         item1 = LinkedList.objects.create(name="item1")
    #         LinkedList.objects.create(name="item2", previous_item=item1)
    #         item1_db = LinkedList.objects.select_related("next_item").get(name="item1")
    #         self.assertEqual(item1_db.next_item.name, "item2")
        