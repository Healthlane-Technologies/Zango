
import os
from alembic.config import Config
from alembic import command
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from zelthy3.sql_alchemy import engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Set up the Alembic configuration
alembic_cfg = Config()
alembic_cfg.set_main_option("script_location", "zelthy_apps/Tenant3/migrations")
alembic_cfg.set_main_option("sqlalchemy.url", 'postgresql://postgres:zelthy3pass@localhost/postgres')

# Run the migrations
command.revision(alembic_cfg, message='added field')

# Delete env.py
command.upgrade(alembic_cfg, 'head')

# command.downgrade(alembic_cfg, '-1')
