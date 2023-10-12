import click

from zelthy.core.package_utils import install_package as install_pkg


@click.command("install-package")
@click.argument("package_name")
@click.option("--version", prompt=True, help="Version", default="latest")
@click.option("--tenants", prompt=True, help="Tenants")
@click.option("--skip-static", is_flag=True, help="Skip Static")
@click.option("--skip-migrate", is_flag=True, help="Skip Migrate")
def install_package(package_name, version, tenants, skip_static, skip_migrate):
    for tenant in tenants.split(","):
        result = install_pkg(package_name, version, tenant)
        click.echo(result)
