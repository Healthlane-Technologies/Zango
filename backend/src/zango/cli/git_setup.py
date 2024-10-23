import json
import os

import click
import git


def is_valid_app_directory(directory):
    # Define your validation criteria
    required_files = ["settings.json", "manifest.json"]

    for file in required_files:
        if not os.path.isfile(os.path.join(directory, file)):
            return False

    return True


def update_settings_with_git_repo_url(
    app_directory, git_repo_url, dev_branch, staging_branch, prod_branch
):
    """
    Update the 'git_repo_url' in the 'settings.json' file located in the app directory.

    Args:
    - app_directory (str): Full path of the app directory.
    - git_repo_url (str): URL of the remote git repository.

    Returns:
    - bool: True if successful, False otherwise.
    """
    settings_file_path = os.path.join(app_directory, "settings.json")

    try:
        # Load current settings from settings.json
        with open(settings_file_path, "r") as settings_file:
            settings = json.load(settings_file)

        # Update git_repo_url in settings
        git_config = settings.get("git_config", {})
        git_config["repo_url"] = git_repo_url
        git_branch = git_config.get("branch", {})
        git_branch.update(
            {"dev": dev_branch, "staging": staging_branch, "prod": prod_branch}
        )
        git_config["branch"] = git_branch
        settings["git_config"] = git_config

        # Write updated settings back to settings.json
        with open(settings_file_path, "w") as settings_file:
            json.dump(settings, settings_file, indent=4)

        return True

    except FileNotFoundError:
        click.echo(f"Error: settings.json not found in {app_directory}.")
    except json.JSONDecodeError:
        click.echo(f"Error: settings.json is not valid JSON in {app_directory}.")
    except Exception as e:
        click.echo(f"Error occurred while updating settings.json: {e}")

    return False


@click.command("git-setup")
@click.argument("app_directory", type=click.Path(exists=True, resolve_path=True))
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
    app_directory,
    git_repo_url,
    dev_branch,
    staging_branch,
    prod_branch,
    initialize,
):
    """
    Initialize a git repository in the specified app directory and add the given remote repository URL.

    APP_DIRECTORY: The directory of the app.
    GIT_REPO_URL: The URL of the remote git repository.
    """
    # Check if the app directory exists
    if not os.path.exists(app_directory):
        click.echo(f"The directory {app_directory} does not exist.")
        return

    # Validate if the app directory is valid
    if not is_valid_app_directory(app_directory):
        click.echo(f"The directory {app_directory} is not a valid zango app directory.")
        return

    try:
        if initialize:
            # Initialize git repository
            repo = git.Repo.init(app_directory)

            # Create .gitignore file
            # TODO: Create git files template
            with open(os.path.join(app_directory, ".gitignore"), "w") as gitignore_file:
                gitignore_file.write("venv/\n")
                gitignore_file.write("*.pyc\n")
                gitignore_file.write("__pycache__/\n")
                gitignore_file.write(".DS_Store\n")

            # Create README.md
            with open(os.path.join(app_directory, "README.md"), "w") as readme_file:
                readme_file.write(f"# {os.path.basename(app_directory)}\n")

            # Add remote repository
            origin = repo.create_remote("origin", git_repo_url)

            # Fetch all branches from the remote
            origin.fetch()

            remote_branches = [ref.name.split("/")[-1] for ref in origin.refs]

            # Check if the branch exists locally
            if dev_branch in remote_branches:
                # Checkout the existing branch
                repo.git.checkout(dev_branch)
            else:
                # Create a new branch and checkout
                repo.git.checkout("-b", dev_branch)

            click.echo(
                f"Initialized git repository in {app_directory} and set remote to {git_repo_url}"
            )

        update_settings_with_git_repo_url(
            app_directory, git_repo_url, dev_branch, staging_branch, prod_branch
        )

        click.echo(f"Git setup completed in {app_directory}")

    except Exception as e:
        click.echo(f"An error occurred: {e}")
