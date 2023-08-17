from workspaces.Tenant3.bulk_create.models import BulkAuthor, BulkBook
from zelthy.test_utils.base import BaseTestCase

class BulkCreateTest(BaseTestCase):

    def test_bulk_create(self):
        authors_to_create = [
            BulkAuthor(name="Author A"),
            BulkAuthor(name="Author B"),
            BulkAuthor(name="Author C")
        ]
        BulkAuthor.objects.bulk_create(authors_to_create)

        created_authors = BulkAuthor.objects.all()
        self.assertEqual(created_authors.count(), 3)

    def test_bulk_create_with_related_objects(self):
        author = BulkAuthor.objects.create(name="Author X")

        books_to_create = [
            BulkBook(title="Book 1", author=author, price=20),
            BulkBook(title="Book 2", author=author, price=30),
            BulkBook(title="Book 3", author=author, price=25)
        ]
        BulkBook.objects.bulk_create(books_to_create)

        created_books = BulkBook.objects.filter(author=author)
        self.assertEqual(created_books.count(), 3)
    
    def test_bulk_create_large_number(self):
        authors_to_create = [BulkAuthor(name=f"Author {i}") for i in range(100)]
        BulkAuthor.objects.bulk_create(authors_to_create)

        created_authors = BulkAuthor.objects.all()
        self.assertEqual(created_authors.count(), 100)

    def test_bulk_create_empty_list(self):
        books_to_create = []
        BulkBook.objects.bulk_create(books_to_create)

        created_books = BulkBook.objects.all()
        self.assertEqual(created_books.count(), 0)
        
    def test_bulk_create_with_different_authors(self):
        authors_to_create = [
            BulkAuthor(name="Author A"),
            BulkAuthor(name="Author B"),
            BulkAuthor(name="Author C")
        ]
        BulkAuthor.objects.bulk_create(authors_to_create)

        author_a = BulkAuthor.objects.get(name="Author A")
        author_b = BulkAuthor.objects.get(name="Author B")
        
        books_to_create = [
            BulkBook(title="Book A1", author=author_a, price=20),
            BulkBook(title="Book A2", author=author_a, price=30),
            BulkBook(title="Book B1", author=author_b, price=25)
        ]
        BulkBook.objects.bulk_create(books_to_create)

        author_a_books = BulkBook.objects.filter(author=author_a)
        author_b_books = BulkBook.objects.filter(author=author_b)
        self.assertEqual(author_a_books.count(), 2)
        self.assertEqual(author_b_books.count(), 1)