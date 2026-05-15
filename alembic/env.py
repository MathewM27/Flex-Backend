"""Alembic env, wired to the async engine.

The `target_metadata` is the union of every module's SQLAlchemy `Base`
metadata. As modules are added, import their ORM mapping module here so
autogenerate can see new tables — this is the only place we centralize
metadata, per §11.2 (modules own their tables but the migration tool
needs one view).
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

from src.core.config import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject runtime DSN
config.set_main_option("sqlalchemy.url", get_settings().database_url)

# Collect metadata from every module that has an ORM mapping.
# Imports are deferred so adding a module is a one-line change.
from sqlalchemy import MetaData

target_metadata = MetaData()
# Module ORM imports go here, e.g.:
# from src.modules.auth.infrastructure import orm as auth_orm


def _run_migrations(connection):  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_run_migrations)
    await connectable.dispose()


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    asyncio.run(_run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
