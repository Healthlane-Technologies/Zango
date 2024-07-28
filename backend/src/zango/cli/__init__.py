import click
from zango.cli import (
    package_info,
    start_project,
    install_package,
    git_setup,
    update_apps,
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

if __name__ == "__main__":
    cli()
