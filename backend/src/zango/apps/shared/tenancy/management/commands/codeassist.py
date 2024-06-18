import json

from django.core.management.base import BaseCommand
from django.db import connection
from zango.apps.shared.tenancy.models import TenantModel
from zango.apps.dynamic_models.workspace.base import Workspace

from zango.codeassist.user.spec import AppSpec


class Command(BaseCommand):

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "action",
            help="Action to be performed.",
        )
        parser.add_argument(
            "--jsonspec", help="The schema name to be used.", required=True
        )

    def handle(self, *args, **options):
        try:
            if options["action"] == "create":
                try:
                    spec = open(options["jsonspec"], "r").read()
                except Exception as e:
                    raise Exception("Failed to open schema file")

                appspec = AppSpec.model_validate_json(spec)
                appspec.apply()
        except Exception as e:
            import traceback

            print("Exception", e, flush=True)
            print(traceback.format_exc(), flush=True)
