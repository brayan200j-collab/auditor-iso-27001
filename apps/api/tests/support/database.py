"""Test database lifecycle: create `auditor_test`, rebuild the schema with Alembic, truncate."""

from __future__ import annotations

from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine

from auditor.persistence import metadata

API_ROOT = Path(__file__).resolve().parents[2]


def _libpq_url(database_url: str, database: str | None = None) -> str:
    url = make_url(database_url).set(drivername="postgresql")
    if database:
        url = url.set(database=database)
    return url.render_as_string(hide_password=False)


def ensure_database(database_url: str) -> None:
    name = make_url(database_url).database
    with psycopg.connect(_libpq_url(database_url, "postgres"), autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
        if not exists:
            conn.execute(f'CREATE DATABASE "{name}"')


def reset_schema(database_url: str) -> None:
    with psycopg.connect(_libpq_url(database_url), autocommit=True) as conn:
        conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
        conn.execute("CREATE SCHEMA public")
        conn.execute("GRANT USAGE ON SCHEMA public TO public")


def alembic_config(database_url: str) -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def migrate(database_url: str, revision: str = "head") -> None:
    command.upgrade(alembic_config(database_url), revision)


def downgrade(database_url: str, revision: str = "base") -> None:
    command.downgrade(alembic_config(database_url), revision)


def table_names() -> list[str]:
    return [table.name for table in metadata.sorted_tables]


async def truncate_all(engine: AsyncEngine) -> None:
    tables = ", ".join(table_names())
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
