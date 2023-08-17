from django.test import TestCase
from workspaces.Tenant3.one_to_one.models import OneUsr, OneProfile
from zelthy.test.base import BaseTestCase
from django.db import models
from django.db.models import Count, Subquery, OuterRef, F, Q

class OneToOneFieldTest(BaseTestCase):


    def setUp(self):
        self.user1 = OneUsr.objects.create(username="user1", email="user1@example.com")
        self.user2 = OneUsr.objects.create(username="user2", email="user2@example.com")

        self.profile1 = OneProfile.objects.create(user=self.user1, bio="Bio for user1")
        self.profile2 = OneProfile.objects.create(user=self.user2, bio="Bio for user2")
    
    def test_one_to_one_relationship(self):
        self.assertEqual(self.profile1.user, self.user1)
        self.assertEqual(self.profile2.user, self.user2)

    def test_related_name(self):
        user_profile1 = self.user1.oneprofile
        self.assertEqual(user_profile1, self.profile1)

        user_profile2 = self.user2.oneprofile
        self.assertEqual(user_profile2, self.profile2)

    def test_queries(self):
        user_with_profile = OneUsr.objects.get(oneprofile=self.profile1)
        self.assertEqual(user_with_profile, self.user1)

        profile_with_bio = OneProfile.objects.get(user__username="user2")
        self.assertEqual(profile_with_bio, self.profile2)

    def test_related_object_bulk_create(self):
        new_users = [
            OneUsr(username="newuser1", email="newuser1@example.com"),
            OneUsr(username="newuser2", email="newuser2@example.com"),
        ]
        OneUsr.objects.bulk_create(new_users)
        self.assertEqual(OneUsr.objects.count(), 4)

    def test_related_object_unique_constraint(self):
        with self.assertRaises(Exception):
            duplicate_user = OneUsr(username="user1", email="duplicate@example.com")
            duplicate_user.save()

    def test_related_object_update_or_create(self):
        updated_user, created = OneUsr.objects.update_or_create(
            username="user1", defaults={"email": "updated@example.com"}
        )
        self.assertFalse(created)
        self.assertEqual(updated_user.email, "updated@example.com")

    def test_related_object_select_related(self):
        profile_with_user = OneProfile.objects.select_related('user').first()
        self.assertIsNotNone(profile_with_user.user)

    def test_related_object_prefetch_related(self):
        users_with_profiles = OneUsr.objects.prefetch_related('oneprofile').all()
        for user in users_with_profiles:
            self.assertTrue(hasattr(user, 'oneprofile'))

    def test_related_object_values(self):
        users_with_profile_bios = OneUsr.objects.values('username', 'oneprofile__bio').distinct()
        for entry in users_with_profile_bios:
            self.assertIn('username', entry)
            self.assertIn('oneprofile__bio', entry)

    def test_related_object_exists(self):
        user_with_profile = OneUsr.objects.filter(oneprofile__isnull=False).distinct()
        self.assertEqual(user_with_profile.count(), 2)

    def test_related_object_does_not_exist(self):
        with self.assertRaises(OneProfile.DoesNotExist):
            profile_without_user = OneProfile.objects.get(user__username="nonexistent_user")

    def test_related_object_cascade_delete(self):
        profile_id = self.profile1.id
        self.user1.delete()
        with self.assertRaises(OneProfile.DoesNotExist):
            OneProfile.objects.get(id=profile_id)

    
    def test_create_user(self):
        new_user = OneUsr.objects.create(username="newuser", email="newuser@example.com")
        self.assertIsNotNone(new_user.id)

    def test_update_user(self):
        self.user1.username = "updateduser1"
        self.user1.save()
        updated_user = OneUsr.objects.get(id=self.user1.id)
        self.assertEqual(updated_user.username, "updateduser1")

    def test_delete_user(self):
        user_id = self.user1.id
        self.user1.delete()
        with self.assertRaises(OneUsr.DoesNotExist):
            OneUsr.objects.get(id=user_id)


    def test_update_profile(self):
        self.profile1.bio = "Updated bio for user1"
        self.profile1.save()
        updated_profile = OneProfile.objects.get(id=self.profile1.id)
        self.assertEqual(updated_profile.bio, "Updated bio for user1")

    def test_delete_profile(self):
        profile_id = self.profile1.id
        self.profile1.delete()
        with self.assertRaises(OneProfile.DoesNotExist):
            OneProfile.objects.get(id=profile_id)

    def test_query_related_objects(self):
        user_profile = OneUsr.objects.get(username="user1").oneprofile
        self.assertEqual(user_profile, self.profile1)

    def test_reverse_query_related_objects(self):
        users_with_profiles = OneUsr.objects.filter(oneprofile__bio__icontains="Bio")
        self.assertEqual(users_with_profiles.count(), 2)

    def test_related_object_annotation(self):
        users_with_profile_count = OneUsr.objects.annotate(num_profiles=models.Count('oneprofile'))
        for user in users_with_profile_count:
            self.assertTrue(hasattr(user, 'num_profiles'))

    def test_related_object_prefetch_related(self):
        users_with_profiles = OneUsr.objects.prefetch_related('oneprofile').all()
        for user in users_with_profiles:
            self.assertTrue(hasattr(user, 'oneprofile'))

    def test_related_object_select_related(self):
        profile_with_user = OneProfile.objects.select_related('user').first()
        self.assertIsNotNone(profile_with_user.user)

    def test_related_object_exists(self):
        user_with_profile = OneUsr.objects.filter(oneprofile__isnull=False).distinct()
        self.assertEqual(user_with_profile.count(), 2)

    def test_related_object_does_not_exist(self):
        with self.assertRaises(OneProfile.DoesNotExist):
            profile_without_user = OneProfile.objects.get(user__username="nonexistent_user")

    def test_related_object_values(self):
        users_with_profile_bios = OneUsr.objects.values('username', 'oneprofile__bio').distinct()
        for entry in users_with_profile_bios:
            self.assertIn('username', entry)
            self.assertIn('oneprofile__bio', entry)
    
    def test_complex_filtering(self):
        # Test complex filtering with related objects
        complex_filtered_users = OneUsr.objects.filter(
            oneprofile__bio__icontains="Bio"
        )
        self.assertEqual(complex_filtered_users.count(), 2)

    def test_annotation_with_related(self):
        # Test annotation with related objects
        users_with_profile_count = OneUsr.objects.annotate(num_profiles=Count('oneprofile'))
        for user in users_with_profile_count:
            self.assertTrue(hasattr(user, 'num_profiles'))

    def test_subquery_in_filter(self):
        # Test using a subquery in a filter
        users_with_more_than_one_profile = OneUsr.objects.filter(
            id__in=Subquery(
                OneProfile.objects.values('user').annotate(profile_count=Count('id')).filter(profile_count__gt=1).values('user')
            )
        )
        self.assertEqual(users_with_more_than_one_profile.count(), 0)

    def test_outer_ref_subquery(self):
        # Test using OuterRef in a subquery
        users_with_profiles = OneUsr.objects.filter(
            id=OuterRef('oneprofile__user')
        )
        profiles = OneProfile.objects.annotate(
            user_has_profile=Subquery(users_with_profiles.values('id'))
        )
        for profile in profiles:
            self.assertTrue(hasattr(profile, 'user_has_profile'))

    def test_related_object_aggregation(self):
        # Test complex aggregation using related objects
        users_with_most_profiles = OneUsr.objects.annotate(
            num_profiles=Count('oneprofile')
        ).filter(num_profiles=Subquery(
            OneProfile.objects.values('user').annotate(profile_count=Count('id')).order_by('-profile_count').values('profile_count')[:1]
        ))
        for user in users_with_most_profiles:
            self.assertTrue(hasattr(user, 'num_profiles'))

    def test_related_object_select_related(self):
        profile_with_user = OneProfile.objects.select_related('user').first()
        self.assertIsNotNone(profile_with_user.user)

    def test_related_object_prefetch_related(self):
        users_with_profiles = OneUsr.objects.prefetch_related('oneprofile').all()
        for user in users_with_profiles:
            self.assertTrue(hasattr(user, 'oneprofile'))

    def test_related_object_values(self):
        users_with_profile_bios = OneUsr.objects.values('username', 'oneprofile__bio').distinct()
        for entry in users_with_profile_bios:
            self.assertIn('username', entry)
            self.assertIn('oneprofile__bio', entry)

    def test_related_object_exists(self):
        user_with_profile = OneUsr.objects.filter(oneprofile__isnull=False).distinct()
        self.assertEqual(user_with_profile.count(), 2)

    def test_related_object_does_not_exist(self):
        with self.assertRaises(OneProfile.DoesNotExist):
            profile_without_user = OneProfile.objects.get(user__username="nonexistent_user")
    
    def test_related_object_unique_together(self):
        # Test using unique_together constraint with related objects
        with self.assertRaises(Exception):
            duplicate_profile = OneProfile(user=self.user1, bio="Duplicate Bio")
            duplicate_profile.save()


    def test_related_object_reverse_query(self):
        # Test reverse querying related objects
        profile_users = OneProfile.objects.filter(user__username="user1")
        self.assertEqual(profile_users.count(), 1)

    def test_related_object_chained_queries(self):
        # Test chaining queries with related objects
        users_with_profiles_and_bio = OneUsr.objects.filter(
            oneprofile__bio__icontains="Bio"
        ).annotate(profile_bio=F('oneprofile__bio'))
        for user in users_with_profiles_and_bio:
            self.assertTrue(hasattr(user, 'profile_bio'))

    def test_related_object_complex_queries(self):
        # Test complex queries with Q objects and related objects
        complex_filtered_users = OneUsr.objects.filter(
            Q(oneprofile__bio__icontains="Bio") | Q(oneprofile__bio__icontains="user2")
        )
        self.assertEqual(complex_filtered_users.count(), 2)

    def test_related_object_reverse_filtering(self):
        # Test reverse filtering on related objects
        users_without_profile = OneUsr.objects.filter(oneprofile=None)
        self.assertEqual(users_without_profile.count(), 0)  # Update based on actual count



    def test_related_object_exists_in_subquery(self):
        # Test using exists() in a subquery with related objects
        users_with_profiles = OneUsr.objects.filter(
            id__in=Subquery(
                OneProfile.objects.filter(user=OuterRef('pk')).values('user')
            )
        )
        self.assertEqual(users_with_profiles.count(), 2)