import json
import os
import shutil
import subprocess
import zipfile

import boto3
import requests

from botocore import UNSIGNED
from botocore.config import Config
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from django.conf import settings
from django.core import signing
from django.db import connection

import zango

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


def get_package_manifest(package, version):
    try:
        s3 = boto3.client(
            "s3",
            config=Config(signature_version=UNSIGNED),
        )
        resp = s3.get_object(
            Bucket=settings.PACKAGE_BUCKET_NAME,
            Key=f"packages/{package}/{version}/manifest.json",
        )
        return json.loads(resp["Body"].read().decode("utf-8"))
    except Exception:
        print(f"Manifest not found for package: {package}.{version} ")
        return {}


def dep_check(package, version, manifest, installed_packages):
    if not manifest.get("zango"):
        return True
    zango_version_specifier_set = SpecifierSet(manifest["zango"], prereleases=True)
    if not zango_version_specifier_set.contains(Version(zango.__version__)):
        return False
    for dependency, version in manifest["dependencies"].items():
        if not installed_packages.get(dependency):
            return False
        if not SpecifierSet(version, prereleases=True).contains(
            Version(installed_packages[dependency])
        ):
            return False
    return True


def get_all_packages(request, tenant=None):
    installed_packages = {}
    if tenant is not None:
        installed_packages = get_installed_packages(tenant.name)
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
        if "manifest.json" in name:
            continue
        name = name[9:]
        version = name.split("/")[1]
        name = name.split("/")[0]
        package_manifest = get_package_manifest(name, version)
        if name not in packages.keys():
            packages[name] = {"versions": []}
        if package_manifest:
            if dep_check(name, version, package_manifest, installed_packages):
                if name not in packages:
                    packages[name] = {"versions": [Version(version)]}
                else:
                    packages[name]["versions"].append(Version(version))
        else:
            if name not in packages:
                packages[name] = {"versions": [Version(version)]}
            else:
                packages[name]["versions"].append(Version(version))
        if tenant is not None:
            if installed_packages.get(name):
                packages[name]["status"] = "Installed"
                packages[name]["installed_version"] = installed_packages[name]
            else:
                name = name.split("/")[0]
                packages[name]["status"] = "Not Installed"
    resp_data = []
    for package in packages.keys():
        if packages[package].get("versions"):
            packages[package]["versions"] = sorted(
                packages[package]["versions"], reverse=True
            )
            packages[package]["versions"] = [
                str(version) for version in packages[package]["versions"]
            ]
            packages[package]["config_url"] = None
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
    for package in resp_data:
        url = get_package_configuration_url(request, tenant, package["name"])
        if len(url) > 0:
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    package["config_url"] = (
                        f"{url}?token={signing.dumps(request.user.id)}"
                    )
                else:
                    package["config_url"] = None
            except Exception:
                package["config_url"] = None
    return resp_data


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
                if domain:
                    url = get_current_request_url(request, domain=domain)
                    return f"{url}/{route['re_path'][1:]}configure/"
    return ""


def install_package(package_name, version, tenant, release=False):
    if package_installed(package_name, tenant):
        return "Package already installed"
    try:
        installed_packages = get_installed_packages(tenant)
        package_manifest = get_package_manifest(package_name, version)
        if not dep_check(package_name, version, package_manifest, installed_packages):
            raise Exception(
                "Version of the package not supported by current version of Zango"
            )

        # if not package_is_cached(package_name, version):
        create_directories([f"workspaces/{tenant}/packages"])
        resource = boto3.resource(
            "s3",
            config=Config(signature_version=UNSIGNED),
        )
        bucket = resource.Bucket(settings.PACKAGE_BUCKET_NAME)
        bucket.download_file(
            f"packages/{package_name}/{version}/{package_name}.zip",
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
