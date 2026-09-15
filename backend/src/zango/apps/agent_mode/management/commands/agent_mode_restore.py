from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from zango.apps.shared.tenancy.models import TenantModel


class Command(BaseCommand):
    """Roll a workspace back to a run's pre-run snapshot.

    Agent Mode writes directly into the live workspace with no diff gate, so
    this is the undo. It is a management command rather than an HTTP endpoint
    in v1 deliberately: restoring app code over the network on a live app is
    not a week-one feature.

    The displaced tree is renamed aside rather than deleted, so a mistaken
    restore is itself recoverable.
    """

    help = "Restore an app's workspace from an Agent Mode run's pre-run snapshot."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("app_name", help="The app (workspace) name.")
        parser.add_argument("run_uuid", nargs="?", help="Run UUID. Defaults to latest.")
        parser.add_argument(
            "--list", action="store_true", help="List available snapshots."
        )
        parser.add_argument("--noinput", action="store_true", help="Skip confirmation.")

    def handle(self, *args, **options):
        from zango.apps.agent_mode.models import AgentRun
        from zango.apps.agent_mode.snapshot import restore_snapshot

        name = options["app_name"]
        try:
            tenant = TenantModel.objects.get(name=name)
        except TenantModel.DoesNotExist:
            raise CommandError(f"No app named {name!r}.") from None
        connection.set_tenant(tenant)

        runs = AgentRun.objects.exclude(snapshot_path="").order_by("-queued_at")

        if options["list"]:
            if not runs.exists():
                self.stdout.write("No snapshots recorded for this app.")
                return
            for run in runs[:20]:
                self.stdout.write(
                    f"{run.object_uuid}  {run.status:8s}  "
                    f"{run.queued_at:%Y-%m-%d %H:%M}  {run.title[:50]}"
                )
            return

        if options.get("run_uuid"):
            run = runs.filter(object_uuid=options["run_uuid"]).first()
            if run is None:
                raise CommandError(
                    f"No run {options['run_uuid']!r} with a snapshot for {name!r}."
                )
        else:
            run = runs.first()
            if run is None:
                raise CommandError(f"No snapshots recorded for {name!r}.")

        self.stdout.write(
            f"Restoring {name!r} from run {run.object_uuid} "
            f"({run.queued_at:%Y-%m-%d %H:%M}, status={run.status})."
        )
        if not options["noinput"]:
            answer = input("This replaces the current workspace. Continue? [y/N] ")
            if answer.strip().lower() not in ("y", "yes"):
                self.stdout.write("Aborted.")
                return

        result = restore_snapshot(run.snapshot_path, run.workspace_path)
        self.stdout.write(self.style.SUCCESS(f"Restored {result['restored_to']}"))
        if result.get("previous_tree"):
            self.stdout.write(
                f"The replaced tree was kept at {result['previous_tree']} — "
                "delete it once you are satisfied."
            )
        self.stdout.write(
            self.style.WARNING(
                "Restart the app server and Celery workers so the restored code "
                "is loaded."
            )
        )
