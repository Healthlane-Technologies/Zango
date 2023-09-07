
import argparse
import os
import sys
import django
from alembic import command
from alembic.script import ScriptDirectory

def install_packages(args):
    # Logic to install packages based on the provided arguments
    app_name = args.app_name
    settings_file = args.settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)
    django.setup()
    from django.conf import settings

    return

content = '''\"\"\"
${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
\"\"\"
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''



def get_env_content(schema_name):
    return f"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from sqlalchemy import text

config = context.config
    
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        object.schema == "{schema_name}"
    if name.startswith("platformauth_") or name.startswith("django_") or name.startswith("auth_") or name.startswith("apps_") or name.startswith("knox_"):
        return False
    else:
        return True


def run_migrations_offline() -> None:
    
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={{ "paramstyle": "named" }},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {{}}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    current_tenant = context.get_x_argument(as_dictionary=True).get("{schema_name}")
    with connectable.connect() as connection:
        connection.execute(text('set search_path to "%s"' % current_tenant))
        connection.dialect.default_schema_name = current_tenant
        context.configure(
            connection=connection, 
            target_metadata=None, 
            include_object=include_object,
            version_table_schema="{schema_name}",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

"""



def initialize_migration(args):
    app_name = args.app_name
    settings_file = args.settings
    if not app_name:
        raise Exception("App name is required")
    if not settings_file:
        raise Exception("Settings file is required")
    sys.path.append(os.getcwd())
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)    
    django.setup()
    from django.conf import settings
    from zelthy3.backend.apps.shared.apps.models import AppModel
    app = AppModel.objects.get(name=args.app_name)
    base_dir = settings.BASE_DIR
    app_migration_dir = base_dir / "zelthy_apps" /app_name / 'migrations'
    if not os.path.exists(app_migration_dir):
        os.makedirs(app_migration_dir)
        os.makedirs(app_migration_dir / "versions")
        with open(str(app_migration_dir)+"/script.py.mako", "w") as f:            
            f.write(content)
            f.close()
        with open(str(app_migration_dir)+"/env.py", "w") as f:
            f.write(get_env_content(app.schema_name))
            f.close()

def setup_django(args):
    settings_file = args.settings
    sys.path.append(os.getcwd())
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)    
    django.setup()
    return


def get_alembic_cfg(args):
    from alembic.config import Config    
    # settings_file = args.settings
    # sys.path.append(os.getcwd())
    # os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_file)    
    # django.setup()
    setup_django(args)
    from django.conf import settings
    db_user = settings.DATABASES['default']['USER']
    db_pass = settings.DATABASES['default']['PASSWORD']
    db_host = settings.DATABASES['default']['HOST']
    db_name = settings.DATABASES['default']['NAME']
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
    # Set up the Alembic configuration
    alembic_cfg = Config()
    app_name = args.app_name
    alembic_cfg.set_main_option("script_location", f"zelthy_apps/{app_name}/migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    return alembic_cfg


def create_migration_revision(args):
    alembic_cfg = get_alembic_cfg(args)
    command.revision(alembic_cfg, message=args.message)
    return


import ast

class FunctionVisitor(ast.NodeVisitor):

    def __init__(self, schema):
        self.schema = schema

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr in ['create_table', 'add_column', 'drop_column', 'drop_table']:
            schema_keyword = next((kw for kw in node.keywords if kw.arg == 'schema'), None)
            if schema_keyword is None:
                raise ValueError(f"'schema' argument is not provided in operation {ast.unparse(node)} in function {node.func.attr}")
            if isinstance(schema_keyword.value, ast.Constant) and schema_keyword.value.value != self.schema:
                raise ValueError(f"'schema' is not equal to {self.schema} in operation {ast.unparse(node)} in function {node.func.attr}")
        self.generic_visit(node)

def parse_functions(filename, schema):
    with open(filename, "r") as source:
        tree = ast.parse(source.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in ['upgrade', 'downgrade']:
                FunctionVisitor(schema).visit(node)

def migration_upgrade(args):
    setup_django(args)
    from zelthy3.backend.apps.shared.apps.models import AppModel
    app = AppModel.objects.get(name=args.app_name)
    alembic_cfg = get_alembic_cfg(args)    
    script = ScriptDirectory.from_config(alembic_cfg)
    script_location = script.dir+"/versions"
    for file in os.listdir(script_location):
        if file.endswith(".py"):
            parse_functions(os.path.join(script_location, file),app.schema_name)
    command.upgrade(alembic_cfg, 'head', '--verbose')
    return
    # return "Upgraded successfully"

def migration_downgrade(args):
    alembic_cfg = get_alembic_cfg(args)
    command.downgrade(alembic_cfg, args.down)
    return "Downgraded successfully"

def main():
    parser = argparse.ArgumentParser(prog='zelthy3', description='Zelthy3 CLI')
    subparsers = parser.add_subparsers(dest='command')

    parser_install = subparsers.add_parser('install_packages', help='Install packages')
    parser_install.add_argument('app_name', type=str, help='Name of the app')
    parser_install.add_argument('--settings', type=str, help='Django settings file')

    parser_migration_init = subparsers.add_parser('migration_init', help='Initialize Migration')
    parser_migration_init.add_argument('app_name', type=str, help='Name of the app')
    parser_migration_init.add_argument('--settings', type=str, help='Django settings file')
    
    parser_migration_rev = subparsers.add_parser('migration_rev', help='Migration Revision')
    parser_migration_rev.add_argument('app_name', type=str, help='Name of the app')
    parser_migration_rev.add_argument('--settings', type=str, help='Django settings file')
    parser_migration_rev.add_argument('--message', type=str, help='Revision message')

    parser_migration_upgrade = subparsers.add_parser('migration_upgrade', help='Migration Upgrade')
    parser_migration_upgrade.add_argument('app_name', type=str, help='Name of the app')
    parser_migration_upgrade.add_argument('--settings', type=str, help='Django settings file')

    parser_migration_downgrade = subparsers.add_parser('migration_downgrade', help='Migration Downgrade')
    parser_migration_downgrade.add_argument('app_name', type=str, help='Name of the app')
    parser_migration_downgrade.add_argument('--settings', type=str, help='Django settings file')
    parser_migration_downgrade.add_argument('--down', type=str, help='Downgrade revision')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the appropriate function based on the command
    if args.command == 'install_packages':
        install_packages(args)
    elif args.command == 'migration_init':
        initialize_migration(args)
    elif args.command == 'migration_rev':
        return create_migration_revision(args)
    elif args.command == 'migration_upgrade':
        return migration_upgrade(args)
    elif args.command == 'migration_downgrade':
        return migration_downgrade(args)


if __name__ == '__main__':
    main()