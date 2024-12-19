import json
import os
import re
import subprocess
import sys
import traceback

from pathlib import Path

import click
import git

from packaging import specifiers, version

import django

from django.core.management import call_command


# Determine the project name dynamically
def find_project_name():
    manage_py_dir = Path(os.getcwd())
    for item in manage_py_dir.iterdir():
        if item.is_dir() and (item / "settings.py").exists():
            return item.name
    raise RuntimeError(
        "Cannot find project name. Ensure 'settings.py' is in the project directory."
    )


def get_remote_settings(repo_url, branch):
    # Extract the username, repository, and file path from the repo_url
    import requests

    from django.conf import settings

    # Extract the username, repository, and file path from the repo_url
    repo_parts = repo_url.rstrip(".git").split("/")
    username = repo_parts[-2]
    repo_name = repo_parts[-1]
    file_path = "settings.json"

    # Construct the URL to the GitHub API to get the file content
    api_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{file_path}?ref={branch}"

    headers = {
        "Authorization": f"token {settings.GIT_PASSWORD}",
        "Accept": "application/vnd.github.v3.raw",  # Request the raw file content
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Failed to fetch file {file_path} from branch {branch}. HTTP Status Code: {response.status_code} Response: {response.text}"
        )
        return None


def setup_and_pull(path, repo_url, branch="main"):
    try:
        # Try to open an existing repository
        repo = git.Repo(path)
        if repo.bare:
            raise Exception("Repository is bare")
        print(f"Repository found at {path}")

        # Clean the working directory (remove untracked files and reset to HEAD) exlcuding packages
        repo.git.clean("-fd", "--exclude=packages")
        repo.git.reset("--hard", "HEAD")

        # Check if the branch is the same, if not, checkout the correct branch
        if repo.active_branch.name != branch:
            repo.git.checkout(branch)
            print(f"Checked out branch {branch}")

        # Pull the latest changes from the specified branch
        origin = repo.remote(name="origin")
        origin.pull(branch)

        success = True
        message = f"Successfully pulled from origin/{branch}"

    except git.InvalidGitRepositoryError:
        # If not a repository, initialize a new repository and set up the remote
        print(f"No repository found at {path}, initializing a new one.")

        # Remove manifest.json and settings.json if they exist
        files_to_remove = ["manifest.json", "settings.json"]
        for filename in files_to_remove:
            file_path = os.path.join(path, filename)
            if os.path.exists(file_path):
                os.remove(file_path)

        repo = git.Repo.init(path)
        origin = repo.create_remote("origin", repo_url)

        # Fetch and check out the specified branch
        origin.fetch()
        repo.create_head(branch, origin.refs[branch]).set_tracking_branch(
            origin.refs[branch]
        ).checkout()

        success = True
        message = "Repository initialized and checked out branch {branch}"
    except git.GitCommandError as e:
        success = False
        message = f"An error occurred while executing Git commands: {e}\n{traceback.format_exc()}"
    except Exception as e:
        success = False
        message = f"An error occurred: {e}\n{traceback.format_exc()}"

    return success, message


def run_app_migrations(tenant, app_directory):
    print("Running app migrations...")
    try:
        subprocess.run(["python", "manage.py", "ws_migrate", tenant], check=True)
        print("Migrations ran successfully.")
    except subprocess.CalledProcessError:
        raise Exception("Migrations failed.")


def run_package_migrations(tenant, app_directory):
    # Run package migrations
    print("Running package migrations...")

    updated_app_manifest = json.loads(
        open(os.path.join(app_directory, "manifest.json")).read()
    )

    installed_packages = updated_app_manifest["packages"]

    for package in installed_packages:
        try:
            subprocess.run(
                [
                    "python",
                    "manage.py",
                    "ws_migrate",
                    tenant,
                    "--package",
                    package["name"],
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print("Migrations failed for package: ", package)


def sync_static(tenant):
    try:
        subprocess.run(["python", "manage.py", "sync_static", tenant], check=True)
        print("Static files collected successfully.")
    except subprocess.CalledProcessError:
        raise Exception("Collecting static files failed.")


def collect_static():
    try:
        subprocess.run(
            ["python", "manage.py", "collectstatic", "--noinput"], check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Collecting static files failed: {e}")


def execute_fixtures(tenant_name, last_version, current_version, app_directory):
    from packaging.version import Version

    from django.db import transaction

    release_mod = os.path.join(app_directory, "release")
    if not os.path.exists(release_mod):
        return

    version_dirs = [
        version_dir_name
        for version_dir_name in os.listdir(release_mod)
        if os.path.isdir(os.path.join(release_mod, version_dir_name))
    ]
    version_dirs.sort(key=Version)

    failed_fixture_dict = {}

    for version_dir_name in version_dirs:
        try:
            version_dir = os.path.join(release_mod, version_dir_name)
            if os.path.exists(version_dir) and (
                not last_version
                or (
                    Version(current_version) >= Version(version_dir_name)
                    and Version(version_dir_name) > Version(last_version)
                )
            ):
                click.echo(
                    f"Processing fixture for {tenant_name} and version: {version_dir_name}"
                )
                with transaction.atomic():
                    framework_fixtures_file = os.path.join(
                        version_dir, "fixtures", "framework_fixtures.json"
                    )
                    if os.path.exists(framework_fixtures_file):
                        call_command(
                            "tenant_command",
                            "loaddata",
                            framework_fixtures_file,
                            "--schema",
                            tenant_name,
                        )

                    package_fixtures_file = os.path.join(
                        version_dir, "fixtures", "package_fixtures.json"
                    )
                    if os.path.exists(package_fixtures_file):
                        call_command(
                            "import_fixture",
                            package_fixtures_file,
                            "--workspace",
                            tenant_name,
                        )

                    app_fixtures_file = os.path.join(
                        version_dir, "fixtures", "app_fixtures.json"
                    )
                    if os.path.exists(app_fixtures_file):
                        call_command(
                            "import_fixture",
                            app_fixtures_file,
                            "--workspace",
                            tenant_name,
                        )
        except Exception as e:
            import traceback

            message = f"Failed while processing fixture version {version_dir_name}: {e}\n{traceback.format_exc()}"
            failed_fixture_dict[version_dir_name] = message

            error_message = click.style(
                message,
                fg="red",
                bold=True,
            )
            click.echo(error_message, err=True)
            raise Exception(message)

    return failed_fixture_dict


def sync_workspace(tenant):
    from zango.apps.dynamic_models.workspace.base import Workspace

    ws = Workspace(tenant, request=None, as_systemuser=True)
    ws.ready()
    ws.sync_policies()
    ws.sync_tasks(tenant.name)


def get_last_release():
    from zango.apps.release.models import AppRelease

    last_release = (
        AppRelease.objects.filter(status="released").order_by("-created_at").first()
    )
    return last_release


def extract_release_notes(file_path, version):
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r") as file:
        changelog = file.read()
    # Define regex pattern to match version sections
    pattern = re.compile(
        r"## \[(?P<version>\d+\.\d+\.\d+)\] - (?P<date>\d{4}-\d{2}-\d{2})\n(?P<changes>.*?)(?=## \[\d+\.\d+\.\d+\] - \d{4}-\d{2}-\d{2}|\Z)",
        re.S,
    )

    # Find all matches
    matches = pattern.finditer(changelog)

    for match in matches:
        if match.group("version") == version:
            return {
                "version": match.group("version"),
                "date": match.group("date"),
                "changes": match.group("changes").strip(),
            }

    return None


def same_package_version_exists(package, app_directory):
    existing_package_path = os.path.join(app_directory, "packages", package["name"])
    if not os.path.exists(existing_package_path):
        return False
    existing_package = json.loads(
        open(os.path.join(existing_package_path, "manifest.json")).read()
    )
    return package["version"] == existing_package["version"]


def install_packages(tenant, app_directory):
    from zango.core.package_utils import install_package

    # Run package migrations

    updated_app_manifest = json.loads(
        open(os.path.join(app_directory, "manifest.json")).read()
    )

    installed_packages = updated_app_manifest["packages"]

    for package in installed_packages:
        try:
            if not same_package_version_exists(package, app_directory):
                print(f"Installing package: {package['name']}")
                res = install_package(
                    package["name"], package["version"], tenant.name, True
                )
                print(res)
        except subprocess.CalledProcessError:
            print("Failed to install package: ", package)


def create_release(tenant_name, app_settings, app_directory, git_mode):
    from django.db import connection

    from zango.apps.release.models import AppRelease
    from zango.apps.release.utils import is_version_greater
    from zango.apps.shared.tenancy.models import TenantModel

    tenant = TenantModel.objects.get(name=tenant_name)
    connection.set_tenant(tenant)
    with connection.cursor() as c:
        release = None
        try:
            current_version = app_settings.get("version")
            if not current_version:
                raise ValueError("Version key not found in settings.json")

            latest_commit_hash = None
            if git_mode:
                repo = git.Repo(app_directory)
                latest_commit_hash = repo.head.commit.hexsha

            last_release = get_last_release()
            if not last_release or (
                last_release
                and is_version_greater(current_version, last_release.version)
            ):
                release_notes = extract_release_notes(
                    os.path.join(app_directory, "CHANGELOG.md"), current_version
                )
                release = AppRelease.objects.create(
                    version=current_version,
                    description=(
                        release_notes.get("changes", "NA") if release_notes else "NA"
                    ),
                    status="initiated",
                    last_git_hash=latest_commit_hash,
                )
                click.echo(f"New release initiated with version {current_version}")

                release.status = "in_progress"
                release.save(update_fields=["status"])

                extra_config = tenant.extra_config or {}
                if extra_config.get("sync_packages", True):
                    # install packages
                    install_packages(tenant, app_directory)
                else:
                    # simply apply package migrations
                    run_package_migrations(tenant_name, app_directory)

                # Run app migrations
                run_app_migrations(tenant_name, app_directory)

                # Sync Static
                sync_static(tenant_name)

                # Sync workspace
                sync_workspace(tenant)

                last_version = last_release.version if last_release else None
                failed_fixture_dict = execute_fixtures(
                    tenant_name, last_version, current_version, app_directory
                )

                if failed_fixture_dict:
                    release_result = release.release_result or {}
                    steps_dict = release_result.get("steps", {})
                    steps_dict.update(
                        {"fixture": {"failed_fixtures": failed_fixture_dict}}
                    )
                    release_result["steps"] = steps_dict
                    release.release_result = release_result
                    release.save(update_fields=["release_result"])

                release.status = "released"
                release.save(update_fields=["status"])

                return release

                # TODO: Execute the release script

            else:
                print("No version change detected for")

        except Exception as e:
            if release:
                release.status = "failed"
                release.save()
            import traceback

            print(traceback.format_exc())
            raise Exception(f"An error occurred while creating/updating release: {e}")


def is_update_allowed(tenant, app_settings, git_mode=False, repo_url=None, branch=None):
    import zango

    from zango.apps.release.utils import is_version_greater

    local_version = app_settings["version"]
    if git_mode:
        remote_settings = get_remote_settings(repo_url, branch)
        remote_version = remote_settings["version"]
    else:
        remote_settings = app_settings
        remote_version = local_version

    last_release = get_last_release()

    # App name validation
    app_name = remote_settings.get("app_name")
    if app_name != tenant:
        return False, "App name mismatch"

    # Check platform version
    zango_version = remote_settings.get("zango_version")
    if not zango_version:
        return False, "Zango version not found in remote settings"

    installed_zango_version = version.parse(zango.__version__)
    # Compare the installed version with the required version
    try:
        specifier = specifiers.SpecifierSet(zango_version)
        if installed_zango_version not in specifier:
            return (
                False,
                f"Zango version mismatch: Required version: {zango_version}, Installed version: {installed_zango_version}",
            )
    except specifiers.InvalidSpecifier:
        return False, "Invalid Zango version specifier in settings.json"

    if git_mode:
        if is_version_greater(local_version, remote_version) or (
            last_release and is_version_greater(remote_version, last_release.version)
        ):
            return False, "No version change detected"
        else:
            return True, "Update allowed"
    else:
        if last_release and not is_version_greater(local_version, last_release.version):
            return False, "No version change detected"

    return True, "Update allowed"


@click.command("update-apps")
@click.option(
    "--app_name",
    multiple=True,
    required=False,
    help="App Name(s)",
    default=[],
)
def update_apps(app_name):
    project_name = find_project_name()
    project_root = os.getcwd()
    click.echo("Initializing project setup")
    sys.path.insert(0, project_root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_name}.settings")

    django.setup()

    click.echo("Project setup initialized")
    from django.conf import settings
    from django.db import connection

    from zango.apps.shared.tenancy.models import TenantModel

    tenants = TenantModel.objects.filter(status="deployed").exclude(
        tenant_type="shared"
    )
    if app_name:
        click.echo(f"Updating apps: {app_name}")
        tenants = tenants.filter(name__in=app_name)
        if not tenants.exists():
            error_message = click.style(
                f"No app found with names {', '.join(app_name)}", fg="red", bold=True
            )
            click.echo(error_message, err=True)
            sys.exit(1)

    for tenant_obj in tenants:
        tenant = tenant_obj.name
        connection.set_tenant(tenant_obj)

        try:
            app_directory = os.path.join(project_root, "workspaces", tenant)
            app_settings = json.loads(
                open(os.path.join(app_directory, "settings.json")).read()
            )

            repo_url = None
            branch = None
            git_mode = False
            extra_config = tenant_obj.extra_config or {}
            git_settings = extra_config.get("git_config")
            if git_settings and git_settings.get("repo_url", None):
                git_mode = True
                # Initialize git repository
                repo_url = git_settings["repo_url"]

                # Split the repo URL into parts
                parts = repo_url.split("://")

                # Add username and password to the URL
                repo_url = f"{parts[0]}://{settings.GIT_USERNAME}:{settings.GIT_PASSWORD}@{parts[1]}"

                branch = git_settings["branch"].get(settings.ENV, "main")

            update_allowed, message = is_update_allowed(
                tenant, app_settings, git_mode, repo_url, branch
            )
            if not update_allowed:
                error_message = click.style(
                    f"Update not allowed for {tenant}: {message}",
                    fg="red",
                    bold=True,
                )
                click.echo(error_message, err=True)
                continue

            # Pull latest code
            if git_mode:
                pull_status, message = setup_and_pull(app_directory, repo_url, branch)
                if not pull_status:
                    error_message = click.style(
                        f"An error occurred while pulling code: {message}",
                        fg="red",
                        bold=True,
                    )
                    click.echo(error_message, err=True)
                    continue

            app_settings = json.loads(
                open(os.path.join(app_directory, "settings.json")).read()
            )

            # Create entry in release model
            release = create_release(tenant, app_settings, app_directory, git_mode)

            if release:
                success_message = click.style(
                    f"Successfully updated app {tenant} to version {release.version}",
                    fg="green",
                    bold=True,
                )
                click.echo(success_message)

        except Exception as e:
            import traceback

            click.echo(
                f"An error occurred while updating app {tenant}: {traceback.format_exc()}",
            )
