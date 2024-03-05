import os
import click
import json

from zelthy.core.package_utils import get_all_packages


@click.command("list-packages")
@click.option("--tenant", help="Tenant", default=None)
def list_packages(tenant):
    available_packages = get_all_packages()
    tenants = []
    if tenant is not None:
        if os.path.exists("workspaces"):
            if tenant == "all":
                for tenant in os.listdir("workspaces"):
                    tenants.append(tenant)
            else:
                tenants.append(tenant)
            for tenant in os.listdir("workspaces"):
                click.echo(f"List of Packages in Tenant {tenant}")
                with open(f"workspaces/{tenant}/manifest.json", "r") as f:
                    data = json.loads(f.read())
                    packages = data["packages"]
                for package in packages:
                    click.echo(f"{package['name']} : {package['version']}")
        else:
            click.echo("No Workspaces Found, execute command from the project root")
    else:
        click.echo(f"List of available Packages")
        for package in available_packages:
            click.echo(f"{package['name']} : {package['versions']}")
