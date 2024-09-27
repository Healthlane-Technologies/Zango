import click

from zango.cli import initialize_project, install_package, package_info, start_project


@click.group()
def cli():
    """A collection of commands."""
    pass


cli.add_command(start_project.start_project)
cli.add_command(package_info.list_packages)
cli.add_command(install_package.install_package)
cli.add_command(initialize_project.initialize_project)

if __name__ == "__main__":
    cli()
