from workspaces.Tenant3.reverse_lookup.models import ReverseAuthor, ReverseBook
from zelthy.test.base import BaseTestCase
from django.db.models import Count

class ReverseLookupTest(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author1 = ReverseAuthor.objects.create(name="Author 1")
        cls.author2 = ReverseAuthor.objects.create(name="Author 2")

        cls.book1 = ReverseBook.objects.create(title="Book 1", author=cls.author1)
        cls.book2 = ReverseBook.objects.create(title="Book 2", author=cls.author1)
        cls.book3 = ReverseBook.objects.create(title="Book 3", author=cls.author2)
    
    def test_reverse_lookup_books(self):
        self.assertEqual(self.author1.reverse_books.count(), 2)
        self.assertEqual(self.author2.reverse_books.count(), 1)

    def test_reverse_lookup_related_objects(self):
        author_books = self.author1.reverse_books.all()
        self.assertEqual(author_books.count(), 2)
        self.assertIn(self.book1, author_books)
        self.assertIn(self.book2, author_books)
        self.assertNotIn(self.book3, author_books)

    def test_reverse_lookup_single_object(self):
        book_author = self.book1.author
        self.assertEqual(book_author, self.author1)

    def test_reverse_lookup_related_objects_query(self):
        author1_books = self.author1.reverse_books.all()
        self.assertEqual(author1_books.count(), 2)
        self.assertIn(self.book1, author1_books)
        self.assertIn(self.book2, author1_books)
        self.assertNotIn(self.book3, author1_books)

    def test_reverse_lookup_related_objects_values(self):
        author1_book_titles = self.author1.reverse_books.values('title')
        self.assertEqual(author1_book_titles.count(), 2)

    def test_reverse_lookup_related_objects_ordering(self):
        ordered_author1_books = self.author1.reverse_books.order_by('-title')
        self.assertEqual(ordered_author1_books[0], self.book2)
        self.assertEqual(ordered_author1_books[1], self.book1)

    def test_reverse_lookup_related_objects_filter(self):
        specific_author1_book = self.author1.reverse_books.filter(title="Book 1").first()
        self.assertEqual(specific_author1_book, self.book1)

    def test_reverse_lookup_related_objects_aggregation(self):
        from django.db.models import Count
        author_with_max_books = ReverseAuthor.objects.annotate(num_books=Count('reverse_books')).order_by('-num_books').first()
        self.assertIsNotNone(author_with_max_books)
        self.assertEqual(author_with_max_books.num_books, 2)

    def test_reverse_lookup_related_objects_subquery(self):
        authors_with_multiple_books = ReverseAuthor.objects.filter(
            id__in=ReverseBook.objects.values('author').annotate(num_books=Count('id')).filter(num_books__gt=1).values('author')
        )
        self.assertEqual(authors_with_multiple_books.count(), 1)
