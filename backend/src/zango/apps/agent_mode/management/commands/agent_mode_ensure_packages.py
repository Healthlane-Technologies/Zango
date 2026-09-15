from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from zango.apps.shared.tenancy.models import TenantModel


class Command(BaseCommand):
    """Install the packages Agent Mode builds against, if missing.

    Exists as a command rather than an inline call because
    `package_utils.install_package` uses relative ``workspaces/...`` paths and
    shells out to `python manage.py`. Both require cwd == BASE_DIR, which a
    Celery worker does not guarantee. Invoking this as a subprocess with an
    explicit cwd is the same approach the post-run pipeline uses, and for the
    same reason.
    """

    help = "Ensure appbuilder, crud and workflow are installed for an app."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("app_name", help="The app (workspace) name.")
        parser.add_argument(
            "--packages",
            default="",
            help="Comma-separated override of the default package set.",
        )

    def handle(self, *args, **options):
        from zango.apps.agent_mode.packages import REQUIRED_PACKAGES, ensure_packages

        name = options["app_name"]
        try:
            tenant = TenantModel.objects.get(name=name)
        except TenantModel.DoesNotExist:
            raise CommandError(f"No app named {name!r}.") from None
        connection.set_tenant(tenant)

        packages = (
            tuple(p.strip() for p in options["packages"].split(",") if p.strip())
            or REQUIRED_PACKAGES
        )

        def emit(message, is_error=False):
            style = self.style.ERROR if is_error else self.style.SUCCESS
            self.stdout.write(style(message) if is_error else message)

        results = ensure_packages(name, packages=packages, emit=emit)

        failed = [r for r in results if not r.ok]
        for r in failed:
            self.stdout.write(self.style.ERROR(f"{r.name}: {r.message[:500]}"))
        if failed:
            raise CommandError(
                "Could not install: " + ", ".join(r.name for r in failed)
            )
        self.stdout.write(
            self.style.SUCCESS(
                "Packages ready: "
                + ", ".join(
                    f"{r.name}{(' ' + r.version) if r.version else ''}" for r in results
                )
            )
        )
