import os

from django.core.management.base import BaseCommand

from zango.codeassist.user.spec import AppSpec


class Command(BaseCommand):

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "action",
            help="Action to be performed.",
        )
        parser.add_argument(
            "--codeassist_endpoint",
            help="The endpoint URL for codeassist.",
            required=True,
        )
        parser.add_argument(
            "--jsonspec", help="The schema name to be used.", required=True
        )

    def handle(self, *args, **options):
        try:
            if options.get("codeassist_endpoint"):
                os.environ["ZANGO_CODEASSIST_URL"] = options["codeassist_endpoint"]
            else:
                raise Exception("codeassist_endpoint is required")
            if options["action"] == "create":
                try:
                    spec = open(options["jsonspec"], "r").read()
                except Exception as e:
                    raise Exception("Failed to open schema file")

                appspec = AppSpec.model_validate_json(spec)
                appspec.apply()
        except Exception as e:
            print("Exception", e)
