import os
import sys

import click
import git

import django

from django.conf import settings

from .update_apps import find_project_name


def is_valid_app_directory(directory):
    # Define your validation criteria
    required_files = ["settings.json", "manifest.json"]

    for file in required_files:
        if not os.path.isfile(os.path.join(directory, file)):
            return False

    return True


def update_settings_with_git_repo_url(
    app_name, git_repo_url, dev_branch, staging_branch, prod_branch
):
    """
    Update the 'git_repo_url' in the TenantMode.extra_config field.

    Args:
    - app_name (str): Full path of the app directory.
    - git_repo_url (str): URL of the remote git repository.
    - dev_branch (str): Name of the development branch.
    - staging_branch (str): Name of the staging branch.
    - prod_branch (str): Name of the production branch.

    Returns:
    - bool: True if successful, False otherwise.
    """

    try:
        project_name = find_project_name()
        project_root = os.getcwd()
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_name}.settings")
        sys.path.insert(0, project_root)
        django.setup()

        from zango.apps.shared.tenancy.models import TenantModel

        # Update git_repo_url in settings
        tenant_obj = TenantModel.objects.get(name=app_name)
        git_config = {}
        if tenant_obj.extra_config:
            git_config = tenant_obj.extra_config.get("git_config", {})
        else:
            git_config["repo_url"] = git_repo_url
        git_branch = git_config.get("branch", {})
        git_branch.update(
            {"dev": dev_branch, "staging": staging_branch, "prod": prod_branch}
        )
        git_config["branch"] = git_branch
        if tenant_obj.extra_config:
            tenant_obj.extra_config.update({"git_config": git_config})
        else:
            tenant_obj.extra_config = {"git_config": git_config}
        tenant_obj.save()

        return True
    except Exception as e:
        click.echo(f"Error occurred while updating tenant extra config: {e}")

    return False


@click.command("git-setup")
@click.argument("app_name", type=str)
@click.option("--git_repo_url", prompt=True, required=True, help="Repo URL")
@click.option(
    "--dev_branch",
    prompt="Development Branch",
    required=True,
    help="Git Branch for Development",
    default="development",
)
@click.option(
    "--staging_branch",
    prompt="Staging Branch",
    required=True,
    help="Git Branch for Staging",
    default="staging",
)
@click.option(
    "--prod_branch",
    prompt="Production Branch",
    required=True,
    help="Git Branch for Production",
    default="main",
)
@click.option(
    "--initialize", is_flag=True, default=False, help="Initialize the repository"
)
def git_setup(
    git_repo_url,
    dev_branch,
    staging_branch,
    prod_branch,
    initialize,
    app_name,
):
    """
    Initialize a git repository in the specified app directory and add the given remote repository URL.

    APP_DIRECTORY: The directory of the app.
    GIT_REPO_URL: The URL of the remote git repository.
    """

    try:
        from zango.apps.shared.tenancy.models import TenantModel

        TenantModel.objects.get(name=app_name)
    except TenantModel.DoesNotExist:
        click.echo(
            f"The app name '{app_name}' provided as an argument is invalid. Please ensure that you have entered the correct app name and try again."
        )
        return

    # Check if the app directory exists
    app_directory = os.path.join("workspaces", app_name)
    if not os.path.exists(app_directory):
        click.echo(f"The directory {app_directory} does not exist.")
        return

    # Validate if the app directory is valid
    if not is_valid_app_directory(app_directory):
        click.echo(f"The directory {app_directory} is not a valid zango app directory.")
        return

    try:
        if initialize:
            os.system(f"rm -rf {app_directory}/.git")
            os.system(f"rm -rf {app_directory}/.gitignore")
            # Initialize git repository
            repo = git.Repo.init(app_directory)

            # Create .gitignore file
            # TODO: Create git files template
            if settings.ENV == "dev":
                with open(
                    os.path.join(app_directory, ".gitignore"), "w"
                ) as gitignore_file:
                    gitignore_file.write("venv/\n")
                    gitignore_file.write("*.pyc\n")
                    gitignore_file.write("__pycache__/\n")
                    gitignore_file.write(".DS_Store\n")
                    gitignore_file.write("node_modules/\n")
                    gitignore_file.write("*.parcel-cache\n")
                    gitignore_file.write("packages\n")

                # Create README.md
                with open(os.path.join(app_directory, "README.md"), "w") as readme_file:
                    readme_file.write(f"# {os.path.basename(app_directory)}\n")

            parts = git_repo_url.split("://")

            # Add username and password to the URL
            repo_url = f"{parts[0]}://{settings.GIT_USERNAME}:{settings.GIT_PASSWORD}@{parts[1]}"

            # Add remote repository
            origin = repo.create_remote("origin", repo_url)

            # Fetch all branches from the remote
            origin.fetch()

            remote_branches = [ref.name.split("/")[-1] for ref in origin.refs]

            # Check if the branch exists locally
            if settings.ENV == "dev" and dev_branch in remote_branches:
                raise Exception(
                    "Can't initialize repository with existing remote branches with same name."
                )
            else:
                # Create a new branch and checkout
                repo.git.checkout("-b", dev_branch)

            if settings.ENV == "staging":
                if staging_branch in remote_branches:
                    repo.git.checkout(staging_branch, force=True)

            if settings.ENV == "prod":
                if prod_branch in remote_branches:
                    repo.git.checkout(prod_branch, force=True)

            click.echo(
                f"Initialized git repository in {app_directory} and set remote to {git_repo_url}"
            )

        update_settings_with_git_repo_url(
            app_name,
            git_repo_url,
            dev_branch,
            staging_branch,
            prod_branch,
        )

        click.echo(f"Git setup completed in {app_directory}")

    except Exception as e:
        import traceback

        traceback.print_exc()
        click.echo(f"An error occurred: {e}")
