from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine
import asyncio
from alembic import context
import os
import sys
from pathlib import Path

# Add parent directory to path to import our models
sys.path.append(str(Path(__file__).parent.parent))

from models_postgres import Base

# Database URL priority: DATABASE_URL_MIGRATIONS > DATABASE_URL > fallback SQLite
MIGRATIONS_URL = os.getenv("DATABASE_URL_MIGRATIONS") or os.getenv("DATABASE_URL") or "sqlite:///./skyride_temp.db"

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Set the database URL from environment - use fallback for migration generation
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL_ALEMBIC", "sqlite:///./skyride_temp.db"))

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """In this scenario we need to create an Engine and associate a connection with the context."""
    from sqlalchemy.ext.asyncio import create_async_engine
    
    connectable = create_async_engine(MIGRATIONS_URL, future=True)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Use simple sync engine for migration generation
    from sqlalchemy import create_engine
    
    # Convert async URL to sync for Alembic compatibility
    sync_url = MIGRATIONS_URL.replace("postgresql://", "postgresql+psycopg2://").replace("+asyncpg", "")
    
    # Override config URL with our migrations URL
    config.set_main_option("sqlalchemy.url", sync_url)
    connectable = create_engine(sync_url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
