from __future__ import annotations

"""
Alembic environment configuration with full async support.

Key design decisions:
  - The database URL is loaded from the ``DATABASE_URL`` environment variable
    (or from a ``.env`` file via ``pydantic-settings``), never hardcoded.
  - The async SQLAlchemy engine created in ``app.database`` is re-used here so
    that the same connection pool settings apply.
  - All ORM models are imported through ``app.models`` so that Alembic's
    autogenerate feature can detect schema changes.
  - ``render_as_batch=True`` is NOT set because PostgreSQL supports ``ALTER``
    natively; this option is only needed for SQLite.

Usage:
    # Generate a new revision
    alembic revision --autogenerate -m "describe your change"

    # Apply pending migrations
    alembic upgrade head

    # Roll back one step
    alembic downgrade -1
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# ---------------------------------------------------------------------------
# Make the app package importable when Alembic is run from apps/api/
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Import settings and ORM base AFTER adjusting sys.path
# ---------------------------------------------------------------------------

from app.config import get_settings  # noqa: E402
from app.database import Base  # noqa: E402
import app.models  # noqa: E402, F401  — registers all models with the mapper

# ---------------------------------------------------------------------------
# Alembic Config object (gives access to alembic.ini values)
# ---------------------------------------------------------------------------

config = context.config

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Metadata used by autogenerate
# ---------------------------------------------------------------------------

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Runtime database URL
# ---------------------------------------------------------------------------


def _get_db_url() -> str:
    """
    Resolve the database URL in order of precedence:
      1. ``-x db_url=...`` passed on the Alembic CLI.
      2. ``DATABASE_URL`` environment variable.
      3. Pydantic settings (reads from .env file).
    """
    x_args: dict = context.get_x_argument(as_dictionary=True)
    if "db_url" in x_args:
        return x_args["db_url"]

    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    return get_settings().database_url


# ---------------------------------------------------------------------------
# Offline migrations (generate SQL without a live connection)
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Configures the context with only a URL (no engine / connection).
    Calls to ``context.execute()`` emit SQL to a script rather than
    a live database.
    """
    url = _get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (async, against a live database)
# ---------------------------------------------------------------------------


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations inside a sync-bridge callback."""
    url = _get_db_url()
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,  # Alembic should not pool connections
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run async migrations from a synchronous entry point."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
