import click
from zelthy.cli import start_project


@click.group()
def cli():
    """A collection of commands."""
    pass


cli.add_command(start_project.start_project)

if __name__ == "__main__":
    cli()
