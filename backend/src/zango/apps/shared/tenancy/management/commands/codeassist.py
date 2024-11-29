import json

import requests

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
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
            # try:
            #     TenantModel.objects.get(name=app_name)
            #     print("App already exists, codeassist will not be applied")
            #     return
            # except TenantModel.DoesNotExist:
            #     pass
            # app, task_id = TenantModel.create(
            #     name=app_name,
            #     schema_name=app_name,
            #     description="",
            #     tenant_type="app",
            #     status="staged",
            #     timezone="Asia/Kolkata",
            #     app_template_name="",
            #     date_format="%d/%m/%Y",
            #     datetime_format="%d %b %Y %I:%M %p",
            # )
            # while app.status == "staged":
            #     print("Waiting for app to start")
            #     sleep(1)
            #     app = TenantModel.objects.get(id=app.id)
            #     if app.status == "deployed":
            #         try:
            #             domain = Domain.objects.create(domain=domain, tenant=app)
            #         except Exception as e:
            #             print(e)
            #         print("App started successfully, proceeding with codeassist")
            #         break
            resp = requests.post(
                f"{options['codeassist_endpoint']}/generate-app-spec",
                json=spec,
                headers={"Content-Type": "application/json"},
            )
            try:
                with open(f"prompt_{app_name}.json", "w") as f:
                    json.dump(resp.json(), f)
            except Exception as e:
                print(resp.text)
            if resp.status_code == 200:
                app_res = requests.post(
                    f"{options['codeassist_endpoint']}/generate-app",
                    json=resp.json(),
                    headers={"Content-Type": "application/json"},
                )

                if app_res.status_code != 200:
                    raise Exception(f"Codeassist failed: {app_res.text}")

                # shutil.rmtree(f"workspaces/{app_name}")

                file_path = f"{app_name}.zip"
                with open(file_path, "wb") as f:
                    for chunk in app_res.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)

            #     with zipfile.ZipFile(file_path, "r") as zip:
            #         zip.extractall(f"workspaces/{app_name}")
            #         # os.remove(file_path)
            #     manifest = json.load(open(f"workspaces/{app_name}/manifest.json", "r"))
            #     os.remove(f"workspaces/{app_name}/manifest.json")
            #     with open(f"workspaces/{app_name}/manifest.json", "w") as f:
            #         f.write(json.dumps({"packages": []}))
            else:
                print(resp.text)
            #     raise Exception("Codeassist failed")
            # try:
            #     subprocess.run(["python", "manage.py", "ws_makemigration", app_name])
            #     with open(f"workspaces/{app_name}/manifest.json", "w") as f:
            #         f.write(json.dumps(manifest, indent=4))
            #     subprocess.run(["zango", "update-apps", "--app_name", app_name])
            # except Exception as e:
            #     print(e)
        except json.JSONDecodeError as e:
            print(f"Error while parsing jsonspec: {e}")
            return
        except Exception as e:
            import traceback

            traceback.print_exc()
