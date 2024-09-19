import json
import os
import shutil
import subprocess
import zipfile

import boto3
import requests

from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError
from packaging.version import Version

from django.conf import settings
from django.core import signing
from django.db import connection

from zango.core.utils import get_current_request_url


def create_directories(dirs):
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)


def get_installed_packages(tenant):
    with open(f"workspaces/{tenant}/manifest.json") as f:
        data = json.loads(f.read())
        packages = data["packages"]
    return {package["name"]: package["version"] for package in packages}


def get_all_packages(request, tenant=None):
    installed_packages = get_installed_packages(tenant.name) if tenant else {}
    s3_public_packages = get_s3_packages(include_private=True)

    packages = merge_package_data(s3_public_packages, installed_packages, tenant)

    resp_data = format_response_data(packages, installed_packages)

    add_config_urls(resp_data, request, tenant)

    return resp_data


def get_s3_packages(include_private=False):
    public_packages = []
    private_packages = []
    s3_public = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    try:
        public_s3_package_data = s3_public.list_objects(
            Bucket=settings.PACKAGE_BUCKET_NAME, Prefix="packages/public/"
        )
        public_packages = public_s3_package_data.get("Contents", [])
    except ClientError as e:
        print(f"Error retrieving public packages: {e}")

    if include_private:
        try:
            s3_private = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=Config(signature_version="s3v4"),
            )

            private_s3_package_data = s3_private.list_objects(
                Bucket=settings.PACKAGE_BUCKET_NAME, Prefix="packages/private/"
            )
            private_packages = private_s3_package_data.get("Contents", [])
        except ClientError as e:
            print(f"Error retrieving private packages: {e}")

    packages = {}
    for package in public_packages + private_packages:
        if package["Key"].endswith("/"):
            continue
        parts = package["Key"].split("/")
        name, version = parts[2], parts[3]
        if name not in packages:
            packages[name] = {"versions": []}
        packages[name]["versions"].append(Version(version))

    return packages


def merge_package_data(s3_public_packages, installed_packages, tenant):
    for name, data in s3_public_packages.items():
        data["versions"] = sorted(data["versions"], reverse=True)
        data["versions"] = [str(version) for version in data["versions"]]
        data["config_url"] = None

        if tenant:
            if name in installed_packages:
                data["status"] = "Installed"
                data["installed_version"] = installed_packages[name]
            else:
                data["status"] = "Not Installed"

    return s3_public_packages


def format_response_data(packages, installed_packages):
    resp_data = [{"name": name, **data} for name, data in packages.items()]

    for name, version in installed_packages.items():
        if name not in packages:
            resp_data.append(
                {
                    "name": name,
                    "status": "Installed",
                    "installed_version": version,
                }
            )

    return resp_data


def add_config_urls(resp_data, request, tenant):
    for package in resp_data:
        url = get_package_configuration_url(request, tenant, package["name"])
        if url:
            resp = requests.get(url)
            if resp.status_code == 200:
                package["config_url"] = f"{url}?token={signing.dumps(request.user.id)}"
            else:
                package["config_url"] = None


def update_settings_json(tenant, package_name, version):
    with open(f"workspaces/{tenant}/settings.json") as f:
        data = json.loads(f.read())

    data["package_routes"].append(
        {"re_path": f"^{package_name}/", "package": f"{package_name}", "url": "urls"}
    )

    with open(f"workspaces/{tenant}/settings.json", "w") as file:
        json.dump(data, file, indent=4)


def update_manifest_json(tenant, package_name, version):
    with open(f"workspaces/{tenant}/manifest.json") as f:
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
    with open(f"workspaces/{tenant.name}/settings.json") as f:
        data = json.loads(f.read())
    for route in data["package_routes"]:
        if route["package"] == package_name:
            domain = tenant.domains.filter(is_primary=True).last()
            url = get_current_request_url(request, domain=domain)
            return f"{url}/{route['re_path'][1:]}configure/"
    return ""


def install_package(package_name, version, tenant, release=False):
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
            f"packages/public/{package_name}/{version}/{package_name}.zip",
            f"workspaces/{tenant}/packages/{package_name}.zip",
        )
        with zipfile.ZipFile(
            f"workspaces/{tenant}/packages/{package_name}.zip", "r"
        ) as zip_ref:
            zip_ref.extractall(f"workspaces/{tenant}/packages")
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
        if not release:
            update_manifest_json(tenant, package_name, version)
            update_settings_json(tenant, package_name, version)

        subprocess.run(f"python manage.py sync_static {tenant}", shell=True)
        subprocess.run("python manage.py collectstatic --noinput", shell=True)
        if os.path.exists(f"workspaces/{tenant}/packages/{package_name}/migrations"):
            subprocess.run(
                f"python manage.py ws_migrate {tenant} --package {package_name}",
                shell=True,
            )
        if not release:
            from zango.apps.dynamic_models.workspace.base import Workspace
            from zango.apps.shared.tenancy.models import TenantModel

            tenant_obj = TenantModel.objects.get(name=tenant)
            connection.set_tenant(tenant_obj)

            with connection.cursor() as c:
                ws = Workspace(connection.tenant, request=None, as_systemuser=True)
                ws.ready()
                ws.sync_policies()
                ws.sync_tasks(tenant)

        return "Package Installed"
    except Exception:
        import traceback

        return f"Package could not be installed\n Error: {traceback.format_exc()}"


def uninstall_package():
    pass


def update_package():
    pass
