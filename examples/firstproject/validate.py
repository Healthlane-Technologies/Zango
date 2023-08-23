import django
from django.db import connection
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "firstproject.settings")
django.setup()

from workspaces.loadtest_0.mod1.models import AggAuthor, AggBook
from django_tenants.utils import get_tenant_model
        

def print_author_table_size(schema_name):
    mod = get_tenant_model().objects.get(schema_name=schema_name)
    connection.set_tenant(mod)
    with connection.cursor() as c:
        size = len(AggAuthor.objects.all())
        print(size)

def print_book_table_size(schema_name):
    mod = get_tenant_model().objects.get(schema_name=schema_name)
    connection.set_tenant(mod)
    with connection.cursor() as c:
        size = len(AggBook.objects.all())
        print(size)

if __name__ == "__main__":
    
    print_author_table_size("loadtest_0")
    print_book_table_size("loadtest_0")