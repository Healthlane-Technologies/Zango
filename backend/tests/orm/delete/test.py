from workspaces.Tenant3.aggregate.models import AggAuthor, AggBook
from zelthy.test.base import BaseTestCase

class DeleteTest(BaseTestCase):

    def setUp(self):
        self.author1 = AggAuthor.objects.create(name="Author 1")
        self.author2 = AggAuthor.objects.create(name="Author 2")

        self.book1 = AggBook.objects.create(title="Book 1", author=self.author1, price=20)
        self.book2 = AggBook.objects.create(title="Book 2", author=self.author1, price=30)
        self.book3 = AggBook.objects.create(title="Book 3", author=self.author2, price=25)
    
    def test_delete_author(self):
        author_count_before_delete = AggAuthor.objects.count()
        self.author1.delete()
        author_count_after_delete = AggAuthor.objects.count()
        self.assertEqual(author_count_after_delete, author_count_before_delete - 1)

    def test_delete_book(self):
        book_count_before_delete = AggBook.objects.count()
        self.book1.delete()
        book_count_after_delete = AggBook.objects.count()
        self.assertEqual(book_count_after_delete, book_count_before_delete - 1)

    def test_delete_author_cascade(self):
        author_count_before_delete = AggAuthor.objects.count()
        self.author1.delete()
        author_count_after_delete = AggAuthor.objects.count()
        self.assertEqual(author_count_after_delete, author_count_before_delete - 1)

        # Check if related books were also deleted
        related_books = AggBook.objects.filter(author=self.author1)
        self.assertEqual(related_books.count(), 0)

    def test_delete_book_restrict(self):
        author1 = AggAuthor.objects.create(name="Author 1")
        book1 = AggBook.objects.create(title="Book 1", author=author1, price=20)
        author1.delete()
        with self.assertRaises(AggBook.DoesNotExist):
            book1.author.delete()

    def test_delete_book_set_null(self):
        author_id = self.book1.author.id
        self.book1.author.delete()
        book_author = AggBook.objects.filter(author_id=author_id).first()
        self.assertIsNone(book_author)

    def test_delete_book_set_default(self):
        author1 = AggAuthor.objects.create(name="Author 1")
        book1 = AggBook.objects.create(title="Book 1", author=author1, price=20)
        author1.delete()
        author_id = book1.author.id
        book1.author.delete()
        book_author = AggBook.objects.filter(author_id=author_id).first()
        self.assertEqual(book_author.author_id, AggAuthor._meta.get_field('name').get_default())

    def test_delete_book_cascade_author(self):
        author1_id = self.author1.id
        self.book1.delete()
        author1 = AggAuthor.objects.filter(id=author1_id).first()
        self.assertIsNotNone(author1)

    def test_delete_multiple_objects(self):
        delete_ids = [self.author1.id, self.author2.id]
        AggAuthor.objects.filter(id__in=delete_ids).delete()

        deleted_authors = AggAuthor.objects.filter(id__in=delete_ids)
        self.assertEqual(deleted_authors.count(), 0)

    def test_delete_all_objects(self):
        AggAuthor.objects.all().delete()

        deleted_authors = AggAuthor.objects.all()
        self.assertEqual(deleted_authors.count(), 0)

    