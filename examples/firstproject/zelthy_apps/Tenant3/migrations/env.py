

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
        object.schema == "tenant3"
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
        dialect_opts={ "paramstyle": "named" },
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    current_tenant = context.get_x_argument(as_dictionary=True).get("tenant3")
    with connectable.connect() as connection:
        connection.execute(text('set search_path to "%s"' % current_tenant))
        connection.dialect.default_schema_name = current_tenant
        context.configure(
            connection=connection, 
            target_metadata=None, 
            include_object=include_object,
            version_table_schema="tenant3",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

