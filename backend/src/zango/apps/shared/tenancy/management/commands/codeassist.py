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
        parser.add_argument(
            "workspace",
            help="The workspace name to be used.",
        )

    def handle(self, *args, **options):
        wks_obj = TenantModel.objects.get(name=options["workspace"])
        connection.set_tenant(wks_obj)
        ws = Workspace(wks_obj, None, True)
        if options["action"] == "create":
            try:
                spec = open(options["jsonspec"], "r").read()
            except Exception as e:
                raise Exception("Failed to open schema file")

            appspec = AppSpec.model_validate_json(spec)
            appspec.apply()
