import boto3
import zipfile
import os
import json
import shutil
import subprocess

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


def create_directories(dirs):
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)


def get_installed_packages(tenant):
    with open(f"workspaces/{tenant}/plugins.json", "r") as f:
        data = json.loads(f.read())
        packages = data["plugins"]
    return {package["name"]: package["version"] for package in packages}


def get_all_packages(tenant=None):
    installed_packages = {}
    if tenant is not None:
        installed_packages = get_installed_packages(tenant)
    packages = {}
    s3_package_data = s3.list_objects(Bucket="zelthy3-packages")
    for package in s3_package_data["Contents"]:
        name = package["Key"]
        if "." in name:
            version = name.split("/")[1]
            name = name.split("/")[0]
            packages[name]["versions"].append(version)
        else:
            name = name.split("/")[0]
            packages[name] = {"versions": []}
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
    return resp_data


def update_settings_json(tenant, package_name, version):
    with open(f"workspaces/{tenant}/settings.json", "r") as f:
        data = json.loads(f.read())

    data["plugin_routes"].append(
        {"re_path": f"^/{package_name}/", "plugin": f"{package_name}", "url": "urls"}
    )

    with open(f"workspaces/{tenant}/settings.json", "w") as file:
        json.dump(data, file, indent=4)


def update_plugins_json(tenant, package_name, version):
    with open(f"workspaces/{tenant}/plugins.json", "r") as f:
        data = json.loads(f.read())

    data["plugins"].append({"name": package_name, "version": version})

    with open(f"workspaces/{tenant}/plugins.json", "w") as file:
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
    if os.path.exists(f"workspaces/{tenant}/plugins/{package_name}/"):
        return True
    else:
        return False


def get_package_configuration_url(package_name, tenant, tenant_domain, port=None):
    with open(f"workspaces/{tenant}/settings.json", "r") as f:
        data = json.loads(f.read())
    for route in data["plugin_routes"]:
        if route["plugin"] == package_name:
            if port is not None:
                return f"{tenant_domain}:{port}/{route['re_path'][1:]}configure/email"
            return f"http://{tenant_domain}/{route['re_path'][1:]}/configure"
    return ""


def install_package(
    package_name, version, tenant, skip_static=False, skip_migrate=False
):
    if package_installed(package_name, tenant):
        return "Package already installed"
    try:
        if not package_is_cached(package_name, version):
            create_directories([f"workspaces/{tenant}/plugins"])
            resource = boto3.resource(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            )
            bucket = resource.Bucket("zelthy3-packages")
            bucket.download_file(
                f"{package_name}/{version}/codebase/",
                f"workspaces/{tenant}/plugins/{package_name}.zip",
            )
            with zipfile.ZipFile(
                f"workspaces/{tenant}/plugins/{package_name}.zip", "r"
            ) as zip_ref:
                zip_ref.extractall(f"workspaces/{tenant}/plugins")
            shutil.move(
                f"workspaces/{tenant}/plugins/pkg-zelthy3-{package_name}-development/{package_name}",
                f"workspaces/{tenant}/plugins/",
            )
            shutil.rmtree(
                f"workspaces/{tenant}/plugins/pkg-zelthy3-{package_name}-development"
            )
            os.remove(f"workspaces/{tenant}/plugins/{package_name}.zip")
            cache_package(
                package_name, version, f"workspaces/{tenant}/plugins/{package_name}"
            )
        else:
            print("Installing from cache")
            create_directories([f"workspaces/{tenant}/plugins"])
            shutil.copytree(
                f"tmp/{package_name}/{version}/",
                f"workspaces/{tenant}/plugins/{package_name}",
            )
        # os.remove(f"workspaces/{tenant}/plugins/{package_name}.zip")
        update_plugins_json(tenant, package_name, version)
        update_settings_json(tenant, package_name, version)

        if not skip_static:
            subprocess.run(f"python manage.py sync_static {tenant}", shell=True)
            subprocess.run("python manage.py collectstatic", shell=True)
        if not skip_migrate:
            subprocess.run(f"python manage.py ws_makemigration {tenant}", shell=True)
            subprocess.run(f"python manage.py ws_migrate {tenant}", shell=True)

        return "Package Installed"
    except Exception as e:
        return f"Package could not be installed\n Error: {str(e)}"


def uninstall_package():
    pass


def update_package():
    pass
