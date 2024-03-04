import os
import zipfile
import json
import shutil
import subprocess
import boto3
from botocore import UNSIGNED
from botocore.config import Config

from django.conf import settings
from django.db import connection

from zelthy.core.utils import get_current_request_url


def create_directories(dirs):
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)


def get_installed_packages(tenant):
    with open(f"workspaces/{tenant}/manifest.json", "r") as f:
        data = json.loads(f.read())
        packages = data["packages"]
    return {package["name"]: package["version"] for package in packages}


def get_all_packages(tenant=None):
    installed_packages = {}
    if tenant is not None:
        installed_packages = get_installed_packages(tenant)
    packages = {}
    s3 = boto3.client(
        "s3",
        config=Config(signature_version=UNSIGNED),
    )
    s3_package_data = s3.list_objects(
        Bucket=settings.PACKAGE_BUCKET_NAME, Prefix="packages/"
    )
    for package in s3_package_data["Contents"]:
        name = package["Key"]
        name = name[9:]
        version = name.split("/")[1]
        name = name.split("/")[0]
        if name not in packages:
            packages[name] = {"versions": [version]}
        else:
            packages[name]["versions"].append(version)
        if tenant is not None:
            if installed_packages.get(name):
                packages[name]["status"] = "Installed"
                packages[name]["installed_version"] = installed_packages[name]
            else:
                name = name.split("/")[0]
                packages[name]["status"] = "Not Installed"
    resp_data = []
    for package, data in packages.items():
        resp_data.append({"name": package, **data})
    for local_package in installed_packages.keys():
        if local_package not in packages.keys():
            resp_data.append(
                {
                    "name": local_package,
                    "status": "Installed",
                    "installed_version": installed_packages[local_package],
                }
            )
    return resp_data


def update_settings_json(tenant, package_name, version):
    with open(f"workspaces/{tenant}/settings.json", "r") as f:
        data = json.loads(f.read())

    data["package_routes"].append(
        {"re_path": f"^{package_name}/", "package": f"{package_name}", "url": "urls"}
    )

    with open(f"workspaces/{tenant}/settings.json", "w") as file:
        json.dump(data, file, indent=4)


def update_manifest_json(tenant, package_name, version):
    with open(f"workspaces/{tenant}/manifest.json", "r") as f:
        data = json.loads(f.read())

    data["packages"].append({"name": package_name, "version": version})

    with open(f"workspaces/{tenant}/manifest.json", "w") as file:
        json.dump(data, file, indent=4)


def cache_package(package_name, version, path):
    create_directories(["tmp", f"tmp/{package_name}"])
    shutil.copytree(path, f"tmp/{package_name}/{version}/")


def package_is_cached(package_name, version):
    if os.path.exists(f"tmp/{package_name}/{version}/"):
        return True
    else:
        return False


def package_installed(package_name, tenant):
    if os.path.exists(f"workspaces/{tenant}/packages/{package_name}/"):
        return True
    else:
        return False


def get_package_configuration_url(request, tenant, package_name):
    with open(f"workspaces/{tenant.name}/settings.json", "r") as f:
        data = json.loads(f.read())
    for route in data["package_routes"]:
        if route["package"] == package_name:
            domain = tenant.domains.filter(is_primary=True).last()
            url = get_current_request_url(request, domain=domain)
            return f"{url}/{route['re_path'][1:]}configure/"
    return ""


def install_package(package_name, version, tenant):
    if package_installed(package_name, tenant):
        return "Package already installed"
    try:
        # if not package_is_cached(package_name, version):
        create_directories([f"workspaces/{tenant}/packages"])
        resource = boto3.resource(
            "s3",
            config=Config(signature_version=UNSIGNED),
        )
        bucket = resource.Bucket(settings.PACKAGE_BUCKET_NAME)
        bucket.download_file(
            f"packages/{package_name}/{version}/codebase/",
            f"workspaces/{tenant}/packages/{package_name}.zip",
        )
        with zipfile.ZipFile(
            f"workspaces/{tenant}/packages/{package_name}.zip", "r"
        ) as zip_ref:
            zip_ref.extractall(f"workspaces/{tenant}/packages")
        shutil.move(
            f"workspaces/{tenant}/packages/pkg-zelthy3-{package_name}-{version}/{package_name}",
            f"workspaces/{tenant}/packages/",
        )
        shutil.rmtree(
            f"workspaces/{tenant}/packages/pkg-zelthy3-{package_name}-{version}"
        )
        os.remove(f"workspaces/{tenant}/packages/{package_name}.zip")
        # cache_package(
        #     package_name, version, f"workspaces/{tenant}/packages/{package_name}"
        # )
        # else:
        #     print("Installing from cache")
        #     create_directories([f"workspaces/{tenant}/packages"])
        #     shutil.copytree(
        #         f"tmp/{package_name}/{version}/",
        #         f"workspaces/{tenant}/packages/{package_name}",
        #     )
        update_manifest_json(tenant, package_name, version)
        update_settings_json(tenant, package_name, version)

        subprocess.run(f"python manage.py sync_static {tenant}", shell=True)
        subprocess.run("python manage.py collectstatic --noinput", shell=True)
        if os.path.exists(f"workspaces/{tenant}/packages/{package_name}/migrations"):
            subprocess.run(
                f"python manage.py ws_migrate {tenant} --package {package_name}",
                shell=True,
            )

        from zelthy.apps.dynamic_models.workspace.base import Workspace
        from zelthy.apps.shared.tenancy.models import TenantModel

        tenant_obj = TenantModel.objects.get(name=tenant)
        connection.set_tenant(tenant_obj)
        with connection.cursor() as c:
            ws = Workspace(connection.tenant, request=None, as_systemuser=True)
            ws.ready()
            ws.sync_tasks(tenant)
            ws.sync_policies()

        return "Package Installed"
    except Exception as e:
        import traceback

        return f"Package could not be installed\n Error: {traceback.format_exc()}"


def uninstall_package():
    pass


def update_package():
    pass
