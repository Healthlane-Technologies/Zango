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


def switch_branch(app_name, branch_name, environment):
    """
    Switch to the specified branch in the app directory if required.

    Args:
    - app_name (str): Name of the application.
    - branch_name (str): Name of the branch to switch to.
    - environment (str): Environment to switch the branch in.
    """

    print(
        f"Switching to branch {branch_name} in {app_name} for {environment} environment"
    )

    if settings.ENV != environment:
        return {
            "success": True,
            "message": "Environment does not match. Skipping branch switch.",
        }

    app_directory = os.path.join("workspaces", app_name)
    if not os.path.exists(app_directory):
        return {
            "success": False,
            "message": f"The directory {app_directory} does not exist.",
        }
    # Validate if the app directory is valid
    if not is_valid_app_directory(app_directory):
        return {
            "success": False,
            "message": f"The directory {app_directory} is not a valid zango app directory.",
        }

    try:
        repo = git.Repo(app_directory)
        if settings.ENV == "dev":
            repo.git.checkout("-b", branch_name)
        else:
            repo.git.checkout(branch_name)
        return {
            "success": True,
            "message": f"Switched to branch {branch_name}",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"An error occurred: {e}",
        }


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
        if git_branch.get("dev") != dev_branch:
            switch_branch(app_name, dev_branch, "dev")
        if git_branch.get("staging") != staging_branch:
            switch_branch(app_name, staging_branch, "staging")
        if git_branch.get("prod") != prod_branch:
            switch_branch(app_name, prod_branch, "prod")
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


def git_setup_function(
    app_name,
    git_repo_url,
    dev_branch="development",
    staging_branch="staging",
    prod_branch="main",
    initialize=False,
):
    """
    Initialize a git repository in the specified app directory and add the given remote repository URL.

    Args:
    - app_name (str): Name of the app.
    - git_repo_url (str): URL of the remote git repository.
    - dev_branch (str): Name of the development branch.
    - staging_branch (str): Name of the staging branch.
    - prod_branch (str): Name of the production branch.
    - initialize (bool): Flag to initialize the repository.

    Returns:
    - dict: Result of the operation.
    """

    try:
        from zango.apps.shared.tenancy.models import TenantModel

        tenant = TenantModel.objects.get(name=app_name)
    except TenantModel.DoesNotExist:
        return {
            "success": False,
            "message": f"The app name '{app_name}' provided as an argument is invalid. Please ensure that you have entered the correct app name and try again.",
        }

    # Check if the app directory exists
    app_directory = os.path.join("workspaces", app_name)
    if not os.path.exists(app_directory):
        return {
            "success": False,
            "message": f"The directory {app_directory} does not exist.",
        }

    # Validate if the app directory is valid
    if not is_valid_app_directory(app_directory):
        return {
            "success": False,
            "message": f"The directory {app_directory} is not a valid zango app directory.",
        }

    try:
        parts = git_repo_url.split("://")
        repo_url = (
            f"{parts[0]}://{settings.GIT_USERNAME}:{settings.GIT_PASSWORD}@{parts[1]}"
        )

        if initialize:
            # Clean up existing git files
            os.system(f"rm -rf {app_directory}/.git")
            os.system(f"rm -rf {app_directory}/.gitignore")

            # Initialize git repository
            repo = git.Repo.init(app_directory)

            # Create .gitignore file
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
                    if tenant.extra_config.get("sync_packages"):
                        gitignore_file.write("packages\n")

                # Create README.md
                with open(os.path.join(app_directory, "README.md"), "w") as readme_file:
                    readme_file.write(f"# {os.path.basename(app_directory)}\n")

            # Add remote repository
            origin = repo.create_remote("origin", repo_url)

            # Fetch all branches from remote
            origin.fetch()

            # Get the default branch from remote
            default_branch = None
            for ref in origin.refs:
                if ref.remote_head == "HEAD":
                    default_branch = ref.reference.remote_head
                    break

            if not default_branch:
                default_branch = "main"

            # Create and checkout main branch
            repo.git.checkout("-b", default_branch)

            # Create initial commit
            repo.index.add(".")
            repo.index.commit("Initial commit")

            # Create dev branch from main
            repo.git.checkout("-b", dev_branch)

        else:
            # Clone the repository if it doesn't exist
            if not os.path.exists(os.path.join(app_directory, ".git")):
                return {
                    "success": False,
                    "message": "Invalid repository, Please initialize the repository first.",
                }
            else:
                repo = git.Repo(app_directory)

            try:
                origin = repo.remote("origin")
            except ValueError:
                origin = repo.create_remote("origin", repo_url)

            # Fetch all branches from remote
            origin.fetch()

            # Get the default branch from remote
            default_branch = None
            for ref in origin.refs:
                if ref.remote_head == "HEAD":
                    default_branch = ref.reference.remote_head
                    break

            if not default_branch:
                default_branch = next(ref.name.split("/")[-1] for ref in origin.refs)

            # Checkout default branch
            repo.git.checkout(default_branch)

            # Create dev branch from default branch if it doesn't exist
            if dev_branch not in [branch.name for branch in repo.heads]:
                repo.git.checkout("-b", dev_branch)

        # Handle environment-specific branch checkouts
        if settings.ENV == "staging" and staging_branch in [
            ref.name.split("/")[-1] for ref in origin.refs
        ]:
            repo.git.checkout(staging_branch, force=True)
        elif settings.ENV == "prod" and prod_branch in [
            ref.name.split("/")[-1] for ref in origin.refs
        ]:
            repo.git.checkout(prod_branch, force=True)

        update_settings_with_git_repo_url(
            app_name,
            git_repo_url,
            dev_branch,
            staging_branch,
            prod_branch,
        )

        return {
            "success": True,
            "message": f"Git setup completed in {app_directory}",
        }

    except Exception as e:
        os.system(f"rm -rf {app_directory}/.git")
        os.system(f"rm -rf {app_directory}/.gitignore")

        tenant.extra_config["git_config"] = {}
        tenant.save()

        import traceback

        traceback.print_exc()
        return {
            "success": False,
            "message": f"An error occurred: {e}",
        }


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
    app_name,
    git_repo_url,
    dev_branch,
    staging_branch,
    prod_branch,
    initialize,
):
    """
    Initialize a git repository in the specified app directory and add the given remote repository URL.
    """
    result = git_setup_function(
        app_name,
        git_repo_url,
        dev_branch,
        staging_branch,
        prod_branch,
        initialize,
    )

    click.echo(result["message"])
