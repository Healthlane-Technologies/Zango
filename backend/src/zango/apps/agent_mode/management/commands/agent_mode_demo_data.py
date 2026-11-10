"""Load an app's demo data: the approved prototype's sample records, written by the build.

    manage.py agent_mode_demo_data <app> [--users <ws>/.zas/test_users.json]

Free design (open mode): the build writes ``backend/demo_data.py`` with

    def load(users):
        '''Replace the app's records with the prototype's sample data; return {entity: count}.'''

``users`` maps each spec role to its test user (AppUserModel), from test_users.json, so the loader
can make them the prototype's personas (rename them, give them the persona's records). The platform
runs it after the API tests, before the screens are compared with the prototype, and once at the end:
what the creator opens shows the prototype's data, not test records. One transaction: a loader that
raises leaves the data as it was.
"""

import importlib
import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from zango.apps.shared.tenancy.models import TenantModel


class Command(BaseCommand):
    help = "Load the app's demo data (backend/demo_data.py load(users))."

    def add_arguments(self, parser):
        parser.add_argument("workspace", help="The workspace (app) name.")
        parser.add_argument(
            "--users", help="test_users.json: the test user per role, passed to load()."
        )

    def handle(self, *args, **options):
        name = options["workspace"]
        try:
            tenant = TenantModel.objects.get(name=name)
        except TenantModel.DoesNotExist:
            raise CommandError(f"No app named {name!r}.") from None
        connection.set_tenant(tenant)
        # the app's modules import as workspaces.<app>.…; Workspace.ready() would load a second copy of
        # each model class, and Django refuses a query that mixes the two
        try:
            module = importlib.import_module(f"workspaces.{name}.backend.demo_data")
        except ModuleNotFoundError as exc:
            if exc.name and exc.name.endswith("demo_data"):
                raise CommandError("no backend/demo_data.py") from None
            raise
        if not callable(getattr(module, "load", None)):
            raise CommandError("backend/demo_data.py has no load(users)")
        users = {}
        if options.get("users"):
            from zango.apps.appauth.models import AppUserModel

            with open(options["users"], encoding="utf-8") as f:
                listed = json.load(f).get("users") or []
            for u in listed:
                user = AppUserModel.objects.filter(email=u.get("email")).first()
                for role in u.get("roles") or []:
                    if user is not None:
                        users.setdefault(role, user)
        with transaction.atomic():
            counts = module.load(users)
            problems = self._check(name)
            if problems:  # rolls the load back: the fix round gets design.demo_data with these lines
                raise CommandError(
                    "backend/demo_data.py left broken records:\n"
                    + "\n".join(problems[:10])
                )
        if options.get("users"):
            self._point_tests_at_demo(name, options["users"])
        self.stdout.write(
            json.dumps(
                {"loaded": counts if isinstance(counts, dict) else {}}, default=str
            )
        )

    @staticmethod
    def _runtime(name, mod):
        try:
            return importlib.import_module(f"workspaces.{name}.backend.zas_core.{mod}")
        except ModuleNotFoundError:
            return None  # an app built before this runtime module existed

    def _check(self, name):
        """What the loader broke that the app's lists and 360s would trip on."""
        demo = self._runtime(name, "demo")
        return demo.check() if demo else []

    def _point_tests_at_demo(self, name, users_path):
        """The load deleted the records the API tests made, so .zas/test_records.json now names records
        that are gone: the design and UI layers would open nothing. Point it at the demo records."""
        spec = self._runtime(name, "spec")
        if spec is None:
            return
        records = {}
        for code in spec.entities():
            try:
                model = spec.model(code)
            except Exception:  # noqa: BLE001
                continue
            ids = model.objects.order_by("-id").values_list("object_uuid", flat=True)[
                :20
            ]
            if ids:
                records[code] = [
                    str(u) for u in reversed(ids)
                ]  # newest last, as the API tests write it
        path = os.path.join(
            os.path.dirname(os.path.abspath(users_path)), "test_records.json"
        )
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=1)
