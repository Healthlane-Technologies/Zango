import click

from zango.cli import (
    git_setup,
    install_package,
    package_info,
    start_project,
    update_apps,
    create_user,
)


@click.group()
def cli():
    """A collection of commands."""
    pass


cli.add_command(start_project.start_project)
cli.add_command(package_info.list_packages)
cli.add_command(install_package.install_package)
cli.add_command(git_setup.git_setup)
cli.add_command(update_apps.update_apps)
cli.add_command(create_user.create_user)

if __name__ == "__main__":
    cli()
