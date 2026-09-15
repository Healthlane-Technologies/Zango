from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from zango.apps.dynamic_models.workspace.base import Workspace
from zango.apps.shared.tenancy.models import TenantModel


class Command(BaseCommand):
    """Sync a workspace's policies, role-policies, tasks and tools.

    Fills a real gap: the equivalent logic exists only as a private
    `sync_workspace()` inside `zango/cli/update_apps.py`, which is
    unreachable without triggering a release — `is_update_allowed()` refuses
    unless settings.json's version exceeds the last AppRelease, and it creates
    release rows. This command does the sync with no release semantics.

    Unlike `ws_makemigration` / `ws_migrate`, an unknown workspace raises
    CommandError rather than dropping into an `input()` loop, so it is safe to
    invoke non-interactively.
    """

    help = "Sync policies, role-policies, tasks and tools for a workspace."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("workspace", help="The workspace (app) name.")
        parser.add_argument(
            "--skip-tools",
            action="store_true",
            help="Skip AppLLMTool discovery from the workspace's tools.py files.",
        )

    def handle(self, *args, **options):
        name = options["workspace"]
        try:
            tenant = TenantModel.objects.get(name=name)
        except TenantModel.DoesNotExist:
            raise CommandError(f"No app named {name!r}.") from None

        connection.set_tenant(tenant)
        ws = Workspace(tenant, request=None, as_systemuser=True)
        ws.ready()

        ws.sync_policies()
        self.stdout.write("policies synced")

        ws.sync_role_policies()
        self.stdout.write("role policies synced")

        ws.sync_tasks(tenant.name)
        self.stdout.write("tasks synced")

        if options.get("skip_tools"):
            self.stdout.write("tools skipped")
        else:
            stats = ws.sync_tools()
            self.stdout.write(f"tools synced: {stats}")

        self.stdout.write(self.style.SUCCESS(f"Workspace {name!r} synced."))
