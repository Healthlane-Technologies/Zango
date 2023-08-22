from django.conf import settings
from django.core.management.base import CommandError, BaseCommand



class Command(BaseCommand):

    def handle(self, *args, **options):
        raise CommandError("startproject has been disabled. Please user startzelthyproject instead.")
        super(Command, self).handle(*args, **options)


# if django_is_in_test_mode():
#     Command = MigrateSchemasCommand