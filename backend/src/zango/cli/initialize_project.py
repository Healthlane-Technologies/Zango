import os
import sys

from pathlib import Path

import click

import django

from django.core.management import call_command

from .start_project import create_platform_user, create_public_tenant, test_db_conection


def generate_env_file(
    project_name,
    db_name,
    db_user,
    db_password,
    db_host,
    db_port,
    redis_host="127.0.0.1",
    redis_port="6379",
):
    env_keys = {
        "POSTGRES_DB": db_name,
        "POSTGRES_USER": db_user,
        "POSTGRES_PASSWORD": db_password,
        "POSTGRES_HOST": db_host,
        "POSTGRES_PORT": db_port,
        "REDIS_HOST": redis_host,
        "REDIS_PORT": redis_port,
        "PROJECT_NAME": project_name,
    }
    project_root = os.path.join(os.getcwd(), project_name)
    env_path = os.path.join(Path(project_root).parent, ".env")
    if not os.path.exists(env_path):
        open(env_path, "w").close()
    fcontent = open(env_path).read()
    with open(env_path, "a+") as f:
        for key, value in env_keys.items():
            if key not in fcontent:
                f.write(f"{key}={value}\n")


@click.command(name="initialize-project")
@click.argument("project_name")
@click.option("--db_name", prompt=True, help="DB Name")
@click.option("--db_user", prompt=True, help="DB User")
@click.option("--db_password", prompt=True, hide_input=True, help="DB Password")
@click.option("--db_host", prompt=True, help="DB Host", default="127.0.0.1")
@click.option("--db_port", prompt=True, help="DB Port", default="5432")
@click.option("--redis_host", prompt=True, help="Redis Host", default="127.0.0.1")
@click.option("--redis_port", prompt=True, help="Redis Port", default="6379")
@click.option("--platform_username", prompt=False, help="Platform Username")
@click.option(
    "--platform_domain_url",
    prompt=False,
    help="Platform Domain URL",
    default="localhost",
)
@click.option(
    "--platform_user_password",
    prompt=False,
    hide_input=True,
    help="Platform User Password",
)
def initialize_project(
    project_name,
    db_name,
    db_user,
    db_password,
    db_host,
    db_port,
    redis_host,
    redis_port,
    platform_username,
    platform_user_password,
    platform_domain_url,
):
    """
    Used to initialize the zango project on an empty db.
    """
    db_connection_status = test_db_conection(
        db_name, db_user, db_password, db_host, db_port
    )
    click.echo(f"db_connection_status: {db_connection_status}")
    if not db_connection_status:
        raise click.ClickException("DB Connection Failed!")

    # Initializing the project
    project_root = os.path.join(os.getcwd(), project_name)
    generate_env_file(
        project_name,
        db_name,
        db_user,
        db_password,
        db_host,
        db_port,
        redis_host,
        redis_port,
    )
    sys.path.insert(0, project_root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_name}.settings")

    django.setup()

    # Migrating Schemas
    call_command("migrate_schemas", schema="public")

    # Creating Public Tenant
    create_public_tenant(platform_domain_url=platform_domain_url)

    # Prompting default platform user details
    while True:
        if not platform_username:
            click.echo("Please enter platform user email")
            platform_username = click.prompt("Email")
        if not platform_user_password:
            platform_user_password = click.prompt(
                "Password", hide_input=True, confirmation_prompt=True
            )

        user_creation_result = create_platform_user(
            platform_username, platform_user_password
        )
        if user_creation_result["success"]:
            break
        else:
            platform_username = None
            platform_user_password = None
            click.echo(user_creation_result["message"])
            retry = click.prompt("Do you want to try again? (yes/no)", default="yes")
            if retry.lower() != "yes":
                raise click.ClickException("User creation aborted by the user.")

    click.echo(user_creation_result["message"])
