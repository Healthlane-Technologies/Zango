from django.test import TestCase
from workspaces.Tenant3.annotate.models import AnnotateAuthor, AnnotateBook
from django.db.models import Count, Sum, Avg, Min, Max
from zelthy.test_utils.base import BaseTestCase

class AnnotateTest(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author1 = AnnotateAuthor.objects.create(name="Author 1")
        cls.author2 = AnnotateAuthor.objects.create(name="Author 2")

        cls.book1 = AnnotateBook.objects.create(title="Book 1", author=cls.author1, price=20)
        cls.book2 = AnnotateBook.objects.create(title="Book 2", author=cls.author1, price=30)
        cls.book3 = AnnotateBook.objects.create(title="Book 3", author=cls.author2, price=25)
    
    def test_annotate_count(self):
        authors_with_book_count = AnnotateAuthor.objects.annotate(book_count=Count('annotatebook'))
        for author in authors_with_book_count:
            if author == self.author1:
                self.assertEqual(author.book_count, 2)
            elif author == self.author2:
                self.assertEqual(author.book_count, 1)

    def test_annotate_sum(self):
        author_total_price = AnnotateAuthor.objects.annotate(total_price=Sum('annotatebook__price'))
        for author in author_total_price:
            if author == self.author1:
                self.assertEqual(author.total_price, 50)
            elif author == self.author2:
                self.assertEqual(author.total_price, 25)

    def test_annotate_avg(self):
        author_avg_price = AnnotateAuthor.objects.annotate(avg_price=Avg('annotatebook__price'))
        for author in author_avg_price:
            if author == self.author1:
                self.assertEqual(author.avg_price, 25)
            elif author == self.author2:
                self.assertEqual(author.avg_price, 25)

    def test_annotate_min(self):
        author_min_price = AnnotateAuthor.objects.annotate(min_price=Min('annotatebook__price'))
        for author in author_min_price:
            if author == self.author1:
                self.assertEqual(author.min_price, 20)
            elif author == self.author2:
                self.assertEqual(author.min_price, 25)

    def test_annotate_max(self):
        author_max_price = AnnotateAuthor.objects.annotate(max_price=Max('annotatebook__price'))
        for author in author_max_price:
            if author == self.author1:
                self.assertEqual(author.max_price, 30)
            elif author == self.author2:
                self.assertEqual(author.max_price, 25)
    
    def test_annotate_related_objects_count(self):
        author1_books = self.author1.annotatebook_set.annotate(other_books_count=Count('author__annotatebook')).first()
        self.assertEqual(author1_books.other_books_count, 2)  # Total of 2 books by both author 1

    def test_annotate_related_objects_sum(self):
        author1_total_price = self.author1.annotatebook_set.annotate(other_books_total_price=Sum('author__annotatebook__price')).first()
        self.assertEqual(author1_total_price.other_books_total_price, 50)  # Total price of two books

    def test_annotate_related_objects_avg(self):
        author1_avg_price = self.author1.annotatebook_set.annotate(other_books_avg_price=Avg('author__annotatebook__price')).first()
        self.assertEqual(author1_avg_price.other_books_avg_price, 25)