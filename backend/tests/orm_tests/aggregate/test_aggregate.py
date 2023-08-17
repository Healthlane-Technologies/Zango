from zelthy.test_utils.base import BaseTestCase
from workspaces.Tenant3.aggregate.models import AggAuthor, AggBook
from django.db.models import Count, Sum, Avg, Min, Max


class AggregationTest(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author1 = AggAuthor.objects.create(name="Author 1")
        cls.author2 = AggAuthor.objects.create(name="Author 2")

        cls.book1 = AggBook.objects.create(title="Book 1", author=cls.author1, price=20)
        cls.book2 = AggBook.objects.create(title="Book 2", author=cls.author1, price=30)
        cls.book3 = AggBook.objects.create(title="Book 3", author=cls.author2, price=25)
    
    def test_count_aggregation(self):
        author_count = AggAuthor.objects.count()
        self.assertEqual(author_count, 2)

    def test_sum_aggregation(self):
        total_price = AggBook.objects.aggregate(total_price=Sum('price'))['total_price']
        self.assertEqual(total_price, 75)

    def test_avg_aggregation(self):
        average_price = AggBook.objects.aggregate(avg_price=Avg('price'))['avg_price']
        self.assertEqual(average_price, 25)

    def test_min_aggregation(self):
        min_price = AggBook.objects.aggregate(min_price=Min('price'))['min_price']
        self.assertEqual(min_price, 20)

    def test_max_aggregation(self):
        max_price = AggBook.objects.aggregate(max_price=Max('price'))['max_price']
        self.assertEqual(max_price, 30)

    def test_group_by_aggregation(self):
        author_book_counts = AggAuthor.objects.annotate(num_books=Count('aggbook'))
        for author in author_book_counts:
            if author == self.author1:
                self.assertEqual(author.num_books, 2)
            elif author == self.author2:
                self.assertEqual(author.num_books, 1)




