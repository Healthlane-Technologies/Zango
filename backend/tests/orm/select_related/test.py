from workspaces.Tenant3.select_related.models import SelectAuthor, SelectBook, SelectUserProfile
from zelthy.test.base import BaseTestCase

class SelectRelatedTest(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = SelectAuthor.objects.create(name="Author 1")
        cls.author2 = SelectAuthor.objects.create(name="author 2")
        cls.author3 = SelectAuthor.objects.create(name="author 3")
        cls.book = SelectBook.objects.create(title="Book 1", author=cls.author)
        cls.book2 = SelectBook.objects.create(title="Book 2", author=cls.author2)

        cls.user_profile = SelectUserProfile.objects.create(author=cls.author, bio="Author's bio")

    def test_select_related_foreign_key(self):
        book = SelectBook.objects.select_related('author').get(title="Book 1")
        self.assertEqual(book.author.name, "Author 1")

    def test_select_related_one_to_one(self):
        profile = SelectUserProfile.objects.select_related('author').get(author__name="Author 1")
        self.assertEqual(profile.author.name, "Author 1")

    def test_select_related_chain(self):
        book = SelectBook.objects.select_related('author__selectuserprofile').get(title="Book 1")
        self.assertEqual(book.author.selectuserprofile.bio, "Author's bio")

    def test_select_related_multiple_objects(self):
        author2 = SelectAuthor.objects.create(name="Author 2")
        book2 = SelectBook.objects.create(title="Book 2", author=author2)
        profile2 = SelectUserProfile.objects.create(author=author2, bio="Author 2's bio")

        books_with_profiles = SelectBook.objects.select_related('author__selectuserprofile')

        for book in books_with_profiles:
            if book == self.book:
                self.assertEqual(book.author.selectuserprofile.bio, "Author's bio")
            elif book == book2:
                self.assertEqual(book.author.selectuserprofile.bio, "Author 2's bio")

    def test_select_related_chain_reverse(self):
        book_profile = SelectBook.objects.select_related('author__selectuserprofile').get(title="Book 1")
        self.assertEqual(book_profile.author.selectuserprofile.author.name, "Author 1")

    