# tests.py
from django.test import TestCase
from workspaces.Tenant3.foreign_key.models import FAuthor, FBook, FPublisher
from django.db.models import Count, Subquery, OuterRef
from zelthy.test.base import BaseTestCase

class ForeignKeyTest(BaseTestCase):

    
    def setUp(self):
        self.author1 = FAuthor.objects.create(name="Author 1", bio="Bio for Author 1")
        self.author2 = FAuthor.objects.create(name="Author 2", bio="Bio for Author 2")

        self.publisher1 = FPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        self.publisher2 = FPublisher.objects.create(name="Publisher 2", website="https://publisher2.com")

        self.book1 = FBook.objects.create(title="Book 1", author=self.author1, publisher=self.publisher1, publication_date="2023-01-01")
        self.book2 = FBook.objects.create(title="Book 2", author=self.author1, publisher=self.publisher2, publication_date="2023-02-01")
        self.book3 = FBook.objects.create(title="Book 3", author=self.author2, publisher=self.publisher1, publication_date="2023-03-01")


    def test_foreign_key_relationship(self):
        self.assertEqual(self.book1.author, self.author1)
        self.assertEqual(self.book2.author, self.author1)
        self.assertEqual(self.book3.author, self.author2)

    def test_related_name(self):
        books_by_author1 = self.author1.fbook_set.all()
        self.assertEqual(books_by_author1.count(), 2)

        books_by_author2 = self.author2.fbook_set.all()
        self.assertEqual(books_by_author2.count(), 1)

    def test_queries(self):
        author = FAuthor.objects.create(name="Author 2", bio="Bio for Author 2")
        publisher = FPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        book1 = FBook.objects.create(title="Book 1", author=author, publisher=publisher, publication_date="2023-01-01")
        book2 = FBook.objects.create(title="Book 2", author=author, publisher=publisher, publication_date="2023-02-01")
        books_by_author1 = FBook.objects.filter(author=author)
        self.assertEqual(books_by_author1.count(), 2)

        authors_of_book1 = book1.author
        self.assertEqual(authors_of_book1, author)

        recent_books = FBook.objects.filter(publication_date__gte="2023-02-01")
        self.assertEqual(recent_books.count(), 3)

    def test_cascade_delete(self):
        author_id = self.author1.id
        self.author1.delete()

        related_books = FBook.objects.filter(author_id=author_id)
        self.assertEqual(related_books.count(), 0)

    def test_update_related_objects(self):
        new_author = FAuthor.objects.create(name="New Author", bio="Bio for New Author")
        publisher = FPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        book1 = FBook.objects.create(title="Book 1", author=self.author1, publisher=publisher, publication_date="2023-01-01")
        book1.author = new_author
        book1.save()

        updated_book = FBook.objects.get(id=book1.id)
        self.assertEqual(updated_book.author, new_author)

    def test_reverse_related_query(self):
        author = FAuthor.objects.create(name="Author 2", bio="Bio for Author 2")
        publisher = FPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        book1 = FBook.objects.create(title="Book 1", author=author, publisher=publisher, publication_date="2023-01-01")
        book2 = FBook.objects.create(title="Book 2", author=author, publisher=publisher, publication_date="2023-02-01")
        author1_books = author.fbook_set.all()
        self.assertEqual(author1_books.count(), 2)

    def test_create_with_foreign_key(self):
        new_book = FBook.objects.create(title="New Book", author=self.author2, publication_date="2023-04-01")
        self.assertEqual(new_book.author, self.author2)

    def test_prefetch_related(self):
        authors_with_books = FAuthor.objects.prefetch_related('fbook_set').all()
        for author in authors_with_books:
            books = author.fbook_set.all()
            self.assertTrue(len(books) >= 0)

    def test_select_related(self):
        book_with_author = FBook.objects.select_related('author').first()
        self.assertIsNotNone(book_with_author.author)
    
    def test_related_object_deletion(self):
        book_to_delete = self.author1.fbook_set.first()
        book_to_delete.delete()
        remaining_books = self.author1.fbook_set.all()
        self.assertEqual(remaining_books.count(), 1)

    def test_related_object_update(self):
        updated_author = FAuthor.objects.create(name="Updated Author", bio="Updated Bio")
        self.book1.author = updated_author
        self.book1.save()
        updated_book = FBook.objects.get(id=self.book1.id)
        self.assertEqual(updated_book.author, updated_author)

    def test_related_object_bulk_create(self):
        new_books = [
            FBook(title="Bulk Book 1", author=self.author1, publication_date="2023-08-01"),
            FBook(title="Bulk Book 2", author=self.author2, publication_date="2023-08-02"),
        ]
        FBook.objects.bulk_create(new_books)
        new_books_count = FBook.objects.filter(title__startswith="Bulk").count()
        self.assertEqual(new_books_count, 2)


    def test_set_null_on_delete(self):
        author = FAuthor.objects.create(name="Author 2", bio="Bio for Author 2")
        publisher = FPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        book1 = FBook.objects.create(title="Book 1", author=author, publisher=publisher, publication_date="2023-01-01")
        publisher_id = publisher.id
        publisher.delete()

        books_with_deleted_publisher = FBook.objects.filter(publisher_id=publisher_id)
        self.assertEqual(books_with_deleted_publisher.count(), 0)

    def test_related_objects_with_null_foreign_key(self):
        books_with_no_publisher = FBook.objects.filter(publisher__isnull=True)
        self.assertEqual(books_with_no_publisher.count(), 0)  # Update based on actual count

    def test_related_object_filtering(self):
        books_by_publisher1 = self.publisher1.fbook_set.all()
        self.assertEqual(books_by_publisher1.count(), 2)

        books_by_author1_publisher2 = self.author1.fbook_set.filter(publisher=self.publisher2)
        self.assertEqual(books_by_author1_publisher2.count(), 1)
    
    def test_related_object_bulk_update(self):
        author = FAuthor.objects.create(name="Author 2", bio="Bio for Author 2")
        publisher = FPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        book1 = FBook.objects.create(title="Book 1", author=author, publisher=publisher, publication_date="2023-01-01")
        book2 = FBook.objects.create(title="Book 2", author=author, publisher=publisher, publication_date="2023-02-01")

        updated_publisher = FPublisher.objects.create(name="Updated Publisher", website="https://updated-publisher.com")
        updated_books_count = FBook.objects.filter(publisher=publisher).update(publisher=updated_publisher)
        self.assertEqual(updated_books_count, 2)

    def test_related_object_ordering(self):
        # Test ordering related objects based on ForeignKey field
        books_ordered_by_author = FBook.objects.order_by('author__name')
        previous_author_name = ''
        for book in books_ordered_by_author:
            self.assertGreaterEqual(book.author.name, previous_author_name)
            previous_author_name = book.author.name

    def test_related_object_aggregation(self):
        from django.db.models import Count
        publishers_with_book_count = FPublisher.objects.annotate(num_books=Count('fbook'))
        for publisher in publishers_with_book_count:
            self.assertTrue(hasattr(publisher, 'num_books'))

    def test_related_object_select_related(self):
        # Test optimizing related object queries with select_related
        book_with_author_and_publisher = FBook.objects.select_related('author', 'publisher').first()
        self.assertIsNotNone(book_with_author_and_publisher.author)
        self.assertIsNotNone(book_with_author_and_publisher.publisher)

    def test_related_object_prefetch_related(self):
        # Test optimizing related object queries with prefetch_related
        authors_with_books_and_publishers = FAuthor.objects.prefetch_related('fbook_set__publisher').all()
        for author in authors_with_books_and_publishers:
            for book in author.fbook_set.all():
                self.assertIsNotNone(book.publisher)

    def test_related_object_exists(self):
        # Test using exists() to check if related objects exist
        author_has_books = FAuthor.objects.filter(fbook__isnull=False).distinct()
        self.assertEqual(author_has_books.count(), 2)

    def test_related_object_values(self):
        # Test using values() to fetch specific fields of related objects
        authors_with_book_titles = FAuthor.objects.values('name', 'fbook__title').distinct()
        for entry in authors_with_book_titles:
            self.assertIn('name', entry)
            self.assertIn('fbook__title', entry)

    def test_related_object_get_or_create(self):
        # Test using get_or_create() with related objects
        new_author, created = FAuthor.objects.get_or_create(name="New Author", bio="New Author Bio")
        new_book, book_created = new_author.fbook_set.get_or_create(title="New Book", publication_date="2023-08-20")
        self.assertTrue(created)
        self.assertTrue(book_created)
        self.assertEqual(new_book.author, new_author)

    def test_related_object_update_or_create(self):
        # Test using update_or_create() with related objects
        existing_author, created = FAuthor.objects.get_or_create(name="Author 1")
        existing_book, book_created = existing_author.fbook_set.update_or_create(
            title="Book 1", defaults={"publication_date": "2023-08-21"}
        )
        self.assertFalse(created)
        self.assertFalse(book_created)
        self.assertEqual(existing_book.author, existing_author)

    def test_related_object_query_with_related_name(self):
        # Test querying related objects using related_name
        publisher_books = self.publisher1.fbook_set.all()
        self.assertEqual(publisher_books.count(), 2)


    # CRUD
    
    def test_create_author(self):
        new_author = FAuthor.objects.create(name="New Author", bio="Bio for New Author")
        self.assertIsNotNone(new_author.id)

    def test_create_publisher(self):
        new_publisher = FPublisher.objects.create(name="New Publisher", website="https://new-publisher.com")
        self.assertIsNotNone(new_publisher.id)

    def test_create_book(self):
        new_book = FBook.objects.create(title="New Book", author=self.author1, publisher=self.publisher1, publication_date="2023-08-01")
        self.assertIsNotNone(new_book.id)

    def test_update_author(self):
        self.author1.name = "Updated Author Name"
        self.author1.save()
        updated_author = FAuthor.objects.get(id=self.author1.id)
        self.assertEqual(updated_author.name, "Updated Author Name")

    def test_update_publisher(self):
        self.publisher2.website = "https://updated-publisher2.com"
        self.publisher2.save()
        updated_publisher = FPublisher.objects.get(id=self.publisher2.id)
        self.assertEqual(updated_publisher.website, "https://updated-publisher2.com")

    def test_update_book(self):
        author = FAuthor.objects.create(name="Author 2", bio="Bio for Author 2")
        publisher = FPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        book1 = FBook.objects.create(title="Book 1", author=author, publisher=publisher, publication_date="2020-01-01")
        book1.title = "Updated Book Title"
        book1.save()
        updated_book = FBook.objects.get(id=book1.id)
        self.assertEqual(updated_book.title, "Updated Book Title")

    def test_delete_author(self):
        author_id = self.author1.id
        self.author1.delete()
        with self.assertRaises(FAuthor.DoesNotExist):
            FAuthor.objects.get(id=author_id)

    def test_delete_publisher(self):
        publisher_id = self.publisher1.id
        self.publisher1.delete()
        with self.assertRaises(FPublisher.DoesNotExist):
            FPublisher.objects.get(id=publisher_id)

    def test_delete_book(self):
        book_id = self.book1.id
        self.book1.delete()
        with self.assertRaises(FBook.DoesNotExist):
            FBook.objects.get(id=book_id)

    def test_related_author_books(self):
        author1_books = self.author1.fbook_set.all()
        self.assertEqual(author1_books.count(), 2)

    def test_related_publisher_books(self):
        author = FAuthor.objects.create(name="Author 2", bio="Bio for Author 2")
        publisher = FPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        book1 = FBook.objects.create(title="Book 1", author=author, publisher=publisher, publication_date="2023-01-01")
        book2 = FBook.objects.create(title="Book 2", author=author, publisher=publisher, publication_date="2023-02-01")
        publisher_books = publisher.fbook_set.all()
        self.assertEqual(publisher_books.count(), 2)

    def test_related_author_name_filtering(self):
        author1_books = FBook.objects.filter(author__name="Author 1")
        self.assertEqual(author1_books.count(), 2)

    def test_related_publisher_website_filtering(self):
        publisher_books = FBook.objects.filter(publisher__website="https://publisher1.com")
        self.assertEqual(publisher_books.count(), 2)

    def test_related_author_aggregation(self):
        from django.db.models import Count
        authors_with_book_count = FAuthor.objects.annotate(num_books=Count('fbook'))
        for author in authors_with_book_count:
            self.assertTrue(hasattr(author, 'num_books'))

    def test_related_publisher_aggregation(self):
        from django.db.models import Count
        publishers_with_book_count = FPublisher.objects.annotate(num_books=Count('fbook'))
        for publisher in publishers_with_book_count:
            self.assertTrue(hasattr(publisher, 'num_books'))
    
    def test_complex_filtering(self):
        # Test complex filtering with related objects
        complex_filtered_books = FBook.objects.filter(author__name="Author 1", publisher__website="https://publisher2.com")
        self.assertEqual(complex_filtered_books.count(), 1)

    def test_annotation_with_related(self):
        # Test annotation with related objects
        authors_with_book_count = FAuthor.objects.annotate(num_books=Count('fbook'))
        for author in authors_with_book_count:
            self.assertTrue(hasattr(author, 'num_books'))

    def test_subquery_in_filter(self):
        # Test using a subquery in a filter
        authors_with_more_than_one_book = FAuthor.objects.filter(
            id__in=Subquery(FBook.objects.values('author').annotate(book_count=Count('id')).filter(book_count__gt=1).values('author'))
        )
        self.assertEqual(authors_with_more_than_one_book.count(), 1)


    def test_complex_related_aggregation(self):
        # Test complex aggregation using related objects
        publishers_with_most_books = FPublisher.objects.annotate(
            num_books=Count('fbook')
        ).filter(num_books=Subquery(
            FBook.objects.values('publisher').annotate(book_count=Count('id')).order_by('-book_count').values('book_count')[:1]
        ))
        for publisher in publishers_with_most_books:
            self.assertTrue(hasattr(publisher, 'num_books'))

    def test_related_object_with_null_values(self):
        # Test related object filtering with null values
        authors_with_no_books = FAuthor.objects.filter(fbook__isnull=True)
        self.assertEqual(authors_with_no_books.count(), 0)