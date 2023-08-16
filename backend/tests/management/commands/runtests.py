from django.core.management.base import BaseCommand
import os
import unittest

class Command(BaseCommand):

    def handle(self, *args, **options):
        unittest.main(module="tests.test_foreign", buffer=True, exit=False)
        unittest.main(module="tests.test_one_to_one", buffer=True, exit=False)