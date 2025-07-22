import os
import sys
import click
import django

from django.core.exceptions import ValidationError


@click.command(name="create-user")
@click.option("--email", prompt=True, help="Email address for the user")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Password for the user")
def create_user(email, password):

    project_name = os.getenv("PROJECT_NAME")
    if not project_name:
        raise click.ClickException("PROJECT_NAME environment variable not set.")
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_name}.settings")
    sys.path.insert(0, os.getcwd())

    django.setup()

    from zango.apps.shared.platformauth.models import PlatformUserModel

    click.echo(f"Creating user with email: {email}")

    try:
        result = PlatformUserModel.create_user(
            name="CLI Created User",
            email=email,
            password=password,
            is_superadmin=True,
            mobile="",
            require_verification=False,
        )
        if result["success"]:
            click.echo("User created successfully.")
        else:
            click.echo(f"Failed to create user: {result['message']}")
    except ValidationError as e:
        raise click.ClickException(f"Validation Error: {str(e)}")
    except Exception as e:
        raise click.ClickException(f"Error: {str(e)}")
