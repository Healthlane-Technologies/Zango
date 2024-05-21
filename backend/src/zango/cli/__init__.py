import click
from zango.cli import package_info, start_project, install_package, generate_project


@click.group()
def cli():
    """A collection of commands."""
    pass


cli.add_command(start_project.start_project)
cli.add_command(package_info.list_packages)
cli.add_command(install_package.install_package)
cli.add_command(generate_project.generate_project)

if __name__ == "__main__":
    cli()
