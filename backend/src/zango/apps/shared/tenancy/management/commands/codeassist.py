import json
import os
import requests
import tarfile
from time import sleep

from django.core.management.base import BaseCommand

from zango.apps.shared.tenancy.models import TenantModel, Domain


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
            spec = json.load(open(options["jsonspec"], "r"))
            app_name = spec["app_name"]
            domain = spec["domain"]
            try:
                TenantModel.objects.get(name=app_name)
                print("App already exists, codeassist will not be applied")
                return
            except TenantModel.DoesNotExist:
                pass
            app, task_id = TenantModel.create(
                name=app_name,
                schema_name=app_name,
                description="",
                tenant_type="app",
                status="staged",
                timezone="Asia/Kolkata",
                date_format="%d/%m/%Y",
                datetime_format="%d %b %Y %I:%M %p",
            )
            while app.status == "staged":
                print("Waiting for app to start")
                sleep(1)
                app = TenantModel.objects.get(id=app.id)
                if app.status == "deployed":
                    try:
                        domain = Domain.objects.create(domain=domain, tenant=app)
                    except Exception as e:
                        print(e)
                    print("App started successfully, proceeding with codeassist")
                    break
            resp = requests.post(
                options["codeassist_endpoint"],
                json=json.dumps(spec),
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                os.removedirs(f"workspaces/{app_name}/")

                file_path = f"{app_name}.tar"
                with open(file_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)

                with tarfile.open(file_path) as tar:
                    tar.extractall(path=f"workspaces/{app_name}/")
                    os.remove(file_path)
        except json.JSONDecodeError as e:
            print(f"Error while parsing jsonspec: {e}")
            return
