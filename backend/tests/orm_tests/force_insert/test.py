from workspaces.test_tenant.force_insert.models import ForceInsertAuthor, ForceInsertBook
from zelthy.test_utils.base import BaseTestCase
from django.db import IntegrityError

class ForceInsertTest(BaseTestCase):

    def test_force_insert(self):
        author = ForceInsertAuthor(name="Author A")
        author.force_insert = True
        author.save()

        created_author = ForceInsertAuthor.objects.get(name="Author A")
        self.assertEqual(created_author.id, author.id)

    def test_force_insert_related(self):
        author = ForceInsertAuthor(name="Author B")
        author.force_insert = True
        author.save()

        book = ForceInsertBook(title="Book X", author=author, price=25)
        book.force_insert = True
        book.save()

        created_book = ForceInsertBook.objects.get(title="Book X")
        self.assertEqual(created_book.id, book.id)
    
    def test_force_insert_multiple_objects(self):
        authors_to_insert = [
            ForceInsertAuthor(name="Author 1"),
            ForceInsertAuthor(name="Author 2"),
            ForceInsertAuthor(name="Author 3")
        ]

        for author in authors_to_insert:
            author.force_insert = True
            author.save()

        created_authors = ForceInsertAuthor.objects.all()
        self.assertEqual(created_authors.count(), len(authors_to_insert))
    
    def test_force_update(self):
        author = ForceInsertAuthor.objects.create(name="one")
        author.name = "2"
        author.save()

        author.name = "3"
        author.save(force_update=True)

        author.name = "4"
        msg = "Cannot force both insert and updating in model saving."
        with self.assertRaisesMessage(ValueError, msg):
            author.save(force_insert=True, force_update=True)



