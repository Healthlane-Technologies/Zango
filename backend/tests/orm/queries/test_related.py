from django.db import models
from workspaces.Tenant3.related.models import RelatedAuthor, RelatedPublisher, RelatedBook, RelatedChapter
from zelthy.test.base import BaseTestCase
from django.db.models import Count, Subquery, OuterRef, F, Q

class ForeignKeyTest(BaseTestCase):

    def setUp(self):
        self.author1 = RelatedAuthor.objects.create(name="Author 1", bio="Bio for Author 1")
        self.author2 = RelatedAuthor.objects.create(name="Author 2", bio="Bio for Author 2")

        self.publisher1 = RelatedPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        self.publisher2 = RelatedPublisher.objects.create(name="Publisher 2", website="https://publisher2.com")

        self.book1 = RelatedBook.objects.create(title="Book 1", author=self.author1, publisher=self.publisher1, publication_date="2023-01-01")
        self.book2 = RelatedBook.objects.create(title="Book 2", author=self.author2, publisher=self.publisher2, publication_date="2023-02-01")

        self.chapter1 = RelatedChapter.objects.create(book=self.book1, title="Chapter 1", order=1)
        self.chapter2 = RelatedChapter.objects.create(book=self.book1, title="Chapter 2", order=2)
        self.chapter3 = RelatedChapter.objects.create(book=self.book2, title="Chapter 1", order=1)
    
    def test_one_to_one_relationship(self):
        self.assertEqual(self.book1.author, self.author1)

    def test_foreign_key_relationship(self):
        self.assertEqual(self.book1.publisher, self.publisher1)

    def test_reverse_foreign_key_query(self):
        chapters_of_book1 = RelatedChapter.objects.filter(book=self.book1)
        self.assertEqual(chapters_of_book1.count(), 2)

    def test_reverse_one_to_one_query(self):
        author_of_book1 = RelatedAuthor.objects.get(relatedbook=self.book1)
        self.assertEqual(author_of_book1, self.author1)


    def test_reverse_foreign_key_ordering(self):
        ordered_chapters = self.book1.relatedchapter_set.order_by('order')
        self.assertEqual(ordered_chapters[0], self.chapter1)
        self.assertEqual(ordered_chapters[1], self.chapter2)

    def test_reverse_foreign_key_filtering(self):
        chapters_with_title = self.book1.relatedchapter_set.filter(title="Chapter 1")
        self.assertEqual(chapters_with_title.count(), 1)

    def test_reverse_foreign_key_aggregation(self):
        from django.db.models import Count
        books_with_chapter_count = RelatedBook.objects.annotate(num_chapters=Count('relatedchapter'))
        for book in books_with_chapter_count:
            self.assertTrue(hasattr(book, 'num_chapters'))

    # def test_related_object_does_not_exist(self):
    #     with self.assertRaises(RelatedAuthor.DoesNotExist):
    #         author_without_book = RelatedAuthor.objects.get(relatedbook=self.book2)

    def test_related_object_exists(self):
        books_with_author = RelatedBook.objects.filter(author__isnull=False).distinct()
        self.assertEqual(books_with_author.count(), 2)

    def test_related_object_bulk_create(self):
        new_authors = [
            RelatedAuthor(name="New Author 1", bio="Bio for New Author 1"),
            RelatedAuthor(name="New Author 2", bio="Bio for New Author 2"),
        ]
        RelatedAuthor.objects.bulk_create(new_authors)
        self.assertEqual(RelatedAuthor.objects.count(), 4)

    def test_related_object_reverse_filtering(self):
        books_with_no_chapters = RelatedBook.objects.filter(relatedchapter=self.chapter3)
        self.assertEqual(books_with_no_chapters.count(), 1) 
    
    def test_reverse_foreign_key_values(self):
        books_with_chapter_titles = RelatedBook.objects.values('title', 'relatedchapter__title').distinct()
        for entry in books_with_chapter_titles:
            self.assertIn('title', entry)
            self.assertIn('relatedchapter__title', entry)

    def test_related_object_unique_together(self):
        # Test using unique_together constraint with related objects
        with self.assertRaises(Exception):
            duplicate_book = RelatedBook(title="Book 1", author=self.author1, publisher=self.publisher1, publication_date="2023-01-01")
            duplicate_book.save()

    def test_related_object_reverse_query(self):
        publisher_books = RelatedPublisher.objects.filter(relatedbook__title="Book 1")
        self.assertEqual(publisher_books.count(), 1)

    def test_related_object_reverse_query_aggregation(self):
        publishers_with_book_count = RelatedPublisher.objects.annotate(num_books=Count('relatedbook'))
        for publisher in publishers_with_book_count:
            self.assertTrue(hasattr(publisher, 'num_books'))

    def test_related_object_reverse_query_values(self):
        publishers_with_book_titles = RelatedPublisher.objects.values('name', 'relatedbook__title').distinct()
        for entry in publishers_with_book_titles:
            self.assertIn('name', entry)
            self.assertIn('relatedbook__title', entry)

    def test_related_object_chained_queries(self):
        authors_with_published_books = RelatedAuthor.objects.filter(
            relatedbook__publisher=self.publisher1
        ).annotate(num_published_books=Count('relatedbook')).filter(num_published_books__gte=1)
        self.assertEqual(authors_with_published_books.count(), 1)

    def test_related_object_subquery(self):
        authors_with_most_chapters = RelatedAuthor.objects.annotate(
            num_chapters=Count('relatedbook__relatedchapter')
        ).order_by('-num_chapters')[:1]
        for author in authors_with_most_chapters:
            self.assertTrue(hasattr(author, 'num_chapters'))

    def test_related_object_select_related(self):
        book_with_author = RelatedBook.objects.select_related('author').first()
        self.assertIsNotNone(book_with_author.author)
    
    def test_related_object_exists_in_subquery(self):
        # Test using exists() in a subquery with related objects
        publishers_with_books = RelatedPublisher.objects.filter(
            id__in=Subquery(
                RelatedBook.objects.filter(publisher=OuterRef('pk')).values('publisher')
            )
        )
        self.assertEqual(publishers_with_books.count(), 2)

    def test_related_object_exists_with_reverse_filter(self):
        authors_with_published_books = RelatedAuthor.objects.filter(
            relatedbook__publisher__isnull=False
        ).distinct()
        self.assertEqual(authors_with_published_books.count(), 2)

    def test_related_object_exists_with_reverse_query(self):
        publishers_with_books = RelatedPublisher.objects.filter(
            relatedbook__isnull=False
        ).distinct()
        self.assertEqual(publishers_with_books.count(), 2)

    def test_related_object_filter_with_related_name(self):
        publisher_with_book = self.publisher1.relatedbook_set.filter(title="Book 1").first()
        self.assertIsNotNone(publisher_with_book)

    def test_related_object_update(self):
        updated_author = RelatedAuthor.objects.get(pk=self.author1.pk)
        updated_author.name = "Updated Author Name"
        updated_author.save()
        self.assertEqual(RelatedAuthor.objects.get(pk=self.author1.pk).name, "Updated Author Name")

    def test_related_object_delete(self):
        author_id = self.author1.pk
        self.author1.delete()
        with self.assertRaises(RelatedAuthor.DoesNotExist):
            RelatedAuthor.objects.get(pk=author_id)

    def test_related_object_reverse_query_with_annotate(self):
        publishers_with_most_chapters = RelatedPublisher.objects.annotate(
            num_chapters=Count('relatedbook__relatedchapter')
        ).order_by('-num_chapters')[:1]
        for publisher in publishers_with_most_chapters:
            self.assertTrue(hasattr(publisher, 'num_chapters'))

    def test_related_object_reverse_query_with_F_expression(self):
        author_with_most_published_books = RelatedAuthor.objects.annotate(
            num_published_books=Count('relatedbook')
        ).order_by('-num_published_books').first()
        self.assertIsNotNone(author_with_most_published_books)

    def test_related_object_reverse_query_with_values(self):
        publishers_with_book_titles = RelatedPublisher.objects.values('name', 'relatedbook__title').distinct()
        for entry in publishers_with_book_titles:
            self.assertIn('name', entry)
            self.assertIn('relatedbook__title', entry)
    
    def test_related_object_reverse_query_with_subquery(self):
        authors_with_max_published_books = RelatedAuthor.objects.annotate(
            num_published_books=Count('relatedbook')
        ).filter(
            num_published_books=Subquery(
                RelatedAuthor.objects.annotate(
                    max_published_books=Count('relatedbook')
                ).filter(pk=OuterRef('pk')).values('max_published_books')
            )
        )
        self.assertEqual(authors_with_max_published_books.count(), 2)

    def test_related_object_reverse_query_with_multiple_levels(self):
        publishers_with_most_chapters = RelatedPublisher.objects.annotate(
            num_chapters=Count('relatedbook__relatedchapter')
        ).filter(
            num_chapters=Subquery(
                RelatedPublisher.objects.annotate(
                    max_chapters=Count('relatedbook__relatedchapter')
                ).filter(pk=OuterRef('pk')).values('max_chapters')
            )
        )
        self.assertEqual(publishers_with_most_chapters.count(), 2)

    def test_related_object_reverse_query_with_conditional_expression(self):
        authors_with_most_published_books = RelatedAuthor.objects.annotate(
            num_published_books=Count('relatedbook')
        ).filter(
            num_published_books=Subquery(
                RelatedAuthor.objects.annotate(
                    max_published_books=Count('relatedbook')
                ).filter(pk=OuterRef('pk')).values('max_published_books')
            )
        )
        self.assertEqual(authors_with_most_published_books.count(), 2)

    def test_related_object_reverse_query_with_related_aggregation(self):
        publishers_with_max_published_books = RelatedPublisher.objects.annotate(
            max_published_books=Count('relatedbook__relatedchapter__book')
        ).filter(
            max_published_books=Subquery(
                RelatedPublisher.objects.annotate(
                    max_published_books=Count('relatedbook__relatedchapter__book')
                ).filter(pk=OuterRef('pk')).values('max_published_books')
            )
        )
        self.assertEqual(publishers_with_max_published_books.count(), 2)


    def test_related_object_reverse_query_with_related_name_ordering(self):
        ordered_chapters = self.publisher1.relatedbook_set.filter(
            author=self.author1
        ).first().relatedchapter_set.order_by('-order')
        self.assertEqual(ordered_chapters[0], self.chapter2)
        self.assertEqual(ordered_chapters[1], self.chapter1)

    
    def test_related_object_filter_with_exact_lookup(self):
        specific_author = RelatedAuthor.objects.filter(name__exact="Author 1").first()
        self.assertEqual(specific_author, self.author1)

    def test_related_object_filter_with_iexact_lookup(self):
        specific_publisher = RelatedPublisher.objects.filter(name__iexact="PUBLISHER 1").first()
        self.assertEqual(specific_publisher, self.publisher1)

    def test_related_object_filter_with_contains_lookup(self):
        books_with_title_containing_1 = RelatedBook.objects.filter(title__contains="1")
        self.assertEqual(books_with_title_containing_1.count(), 1)

    def test_related_object_filter_with_icontains_lookup(self):
        chapters_with_title_containing_1 = RelatedChapter.objects.filter(title__icontains="CHaP")
        self.assertEqual(chapters_with_title_containing_1.count(), 3)

    def test_related_object_filter_with_startswith_lookup(self):
        authors_with_name_starting_with_A = RelatedAuthor.objects.filter(name__startswith="A")
        self.assertEqual(authors_with_name_starting_with_A.count(), 2)

    def test_related_object_filter_with_endswith_lookup(self):
        publishers_with_name_ending_with_2 = RelatedPublisher.objects.filter(name__endswith="2")
        self.assertEqual(publishers_with_name_ending_with_2.count(), 1)

    def test_related_object_filter_with_range_lookup(self):
        books_published_in_january = RelatedBook.objects.filter(publication_date__range=["2023-01-01", "2023-01-31"])
        self.assertEqual(books_published_in_january.count(), 1)

    def test_related_object_filter_with_gt_lookup(self):
        chapters_with_order_greater_than_1 = RelatedChapter.objects.filter(order__gt=1)
        self.assertEqual(chapters_with_order_greater_than_1.count(), 1)

    def test_related_object_filter_with_lt_lookup(self):
        author1 = RelatedAuthor.objects.create(name="Author 1", bio="Bio for Author 1")
        author2 = RelatedAuthor.objects.create(name="Author 2", bio="Bio for Author 2")

        publisher1 = RelatedPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        publisher2 = RelatedPublisher.objects.create(name="Publisher 2", website="https://publisher2.com")

        book1 = RelatedBook.objects.create(title="Book 1", author=author1, publisher=publisher1, publication_date="2023-01-01")
        book2 = RelatedBook.objects.create(title="Book 2", author=author2, publisher=publisher2, publication_date="2023-02-01")
        publishers_with_id_less_than_2 = RelatedPublisher.objects.filter(id__lt=publisher2.id)
        self.assertEqual(publishers_with_id_less_than_2.count(), 3)

    def test_related_object_filter_with_gte_lookup(self):
        chapters_with_order_gte_2 = RelatedChapter.objects.filter(order__gte=2)
        self.assertEqual(chapters_with_order_gte_2.count(), 1)

    def test_related_object_filter_with_lte_lookup(self):
        author1 = RelatedAuthor.objects.create(name="Author 1", bio="Bio for Author 1")
        author2 = RelatedAuthor.objects.create(name="Author 2", bio="Bio for Author 2")

        publisher1 = RelatedPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        publisher2 = RelatedPublisher.objects.create(name="Publisher 2", website="https://publisher2.com")

        book1 = RelatedBook.objects.create(title="Book 1", author=author1, publisher=publisher1, publication_date="2023-01-01")
        book2 = RelatedBook.objects.create(title="Book 2", author=author2, publisher=publisher2, publication_date="2023-02-01")

        publishers_with_id_lte_2 = RelatedPublisher.objects.filter(id__lte=publisher2.id)
        self.assertEqual(publishers_with_id_lte_2.count(), 4)

    def test_related_object_filter_with_in_lookup(self):
        author1 = RelatedAuthor.objects.create(name="Author 1", bio="Bio for Author 1")
        author2 = RelatedAuthor.objects.create(name="Author 2", bio="Bio for Author 2")

        publisher1 = RelatedPublisher.objects.create(name="Publisher 1", website="https://publisher1.com")
        publisher2 = RelatedPublisher.objects.create(name="Publisher 2", website="https://publisher2.com")

        book1 = RelatedBook.objects.create(title="Book 1", author=author1, publisher=publisher1, publication_date="2023-01-01")
        book2 = RelatedBook.objects.create(title="Book 2", author=author2, publisher=publisher2, publication_date="2023-02-01")

        chapter1 = RelatedChapter.objects.create(book=book1, title="Chapter 1", order=1)
        chapter2 = RelatedChapter.objects.create(book=book1, title="Chapter 2", order=2)
        chapter3 = RelatedChapter.objects.create(book=book2, title="Chapter 1", order=1)
        specific_publishers = RelatedPublisher.objects.filter(id__in=[publisher2.id, publisher1.id])
        self.assertEqual(specific_publishers.count(), 2)

    def test_related_object_filter_with_isnull_lookup(self):
        authors_with_null_bio = RelatedAuthor.objects.filter(bio__isnull=True)
        self.assertEqual(authors_with_null_bio.count(), 0)

    def test_related_object_filter_with_exclude_lookup(self):
        publishers_exclude_id_1 = RelatedPublisher.objects.exclude(id=1)
        self.assertEqual(publishers_exclude_id_1.count(), 2)

    def test_related_object_filter_with_or_lookup(self):
        specific_authors = RelatedAuthor.objects.filter(Q(name="Author 1") | Q(name="Author 2"))
        self.assertEqual(specific_authors.count(), 2)

    def test_related_object_filter_with_and_lookup(self):
        specific_books = RelatedBook.objects.filter(Q(title="Book 1") & Q(publisher=self.publisher1))
        self.assertEqual(specific_books.count(), 1)

    def test_related_object_filter_with_negated_lookup(self):
        publishers_not_id_1 = RelatedPublisher.objects.exclude(id=1)
        publishers_with_id_1_negated = RelatedPublisher.objects.filter(~Q(id=1))
        self.assertEqual(publishers_with_id_1_negated.count(), publishers_not_id_1.count())

    def test_related_object_filter_with_complex_expression(self):
        books_published_by_author1_and_chapter_gt_1 = RelatedBook.objects.filter(
            Q(author=self.author1) & Q(relatedchapter__order__gt=1)
        )
        self.assertEqual(books_published_by_author1_and_chapter_gt_1.count(), 1)

    def test_related_object_filter_with_subquery(self):
        authors_with_more_than_one_published_book = RelatedAuthor.objects.filter(
            id__in=Subquery(
                RelatedBook.objects.values('author').annotate(num_books=Count('id')).filter(num_books__gt=1).values('author')
            )
        )
        self.assertEqual(authors_with_more_than_one_published_book.count(), 0)


    def test_related_object_annotate_aggregate(self):
        authors_with_total_published_books = RelatedAuthor.objects.annotate(
            total_published_books=Count('relatedbook')
        )
        for author in authors_with_total_published_books:
            self.assertTrue(hasattr(author, 'total_published_books'))

    def test_related_object_annotate_f_expression(self):
        publishers_with_average_books_per_author = RelatedPublisher.objects.annotate(
            avg_books_per_author=Count('relatedbook__author')
        )
        for publisher in publishers_with_average_books_per_author:
            self.assertTrue(hasattr(publisher, 'avg_books_per_author'))