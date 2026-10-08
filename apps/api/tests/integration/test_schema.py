from __future__ import annotations

from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError, IntegrityError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine

from auditor.persistence import metadata
from tests.support.database import downgrade, ensure_database, migrate, reset_schema, table_names

INSERT_USER = (
    "INSERT INTO users (id, email, full_name, role) VALUES (:id, :email, 'Usuario', 'SME')"
)

EXPECTED_TABLES = {
    "users",
    "companies",
    "company_users",
    "consents",
    "evaluations",
    "analysis_runs",
    "documents",
    "document_chunks",
    "checklist_versions",
    "checklist_items",
    "ai_findings",
    "human_reviews",
    "final_findings",
    "reports",
    "feedback",
    "processing_jobs",
    "llm_calls",
    "audit_logs",
}


def test_data_model_contains_every_required_table() -> None:
    assert set(table_names()) == EXPECTED_TABLES


def test_migrations_are_reversible(database_url: str) -> None:
    scratch = make_url(database_url).set(database="auditor_test_migrations")
    url = scratch.render_as_string(hide_password=False)
    ensure_database(url)
    reset_schema(url)
    migrate(url)
    downgrade(url, "base")
    migrate(url)


async def test_orm_models_match_migrations(engine: AsyncEngine) -> None:
    def _diff(connection: object) -> list[object]:
        context = MigrationContext.configure(connection, opts={"compare_type": True})  # type: ignore[arg-type]
        return compare_metadata(context, metadata)

    async with engine.connect() as connection:
        diff = await connection.run_sync(_diff)
    assert diff == []


async def test_row_level_security_is_enabled_on_every_table(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        rows = await connection.execute(
            text(
                "SELECT relname, relrowsecurity FROM pg_class "
                "WHERE relnamespace = 'public'::regnamespace AND relkind = 'r'"
            )
        )
        flags = dict(rows.all())
    assert set(flags) >= EXPECTED_TABLES
    assert all(flags[table] for table in EXPECTED_TABLES)


@pytest.mark.parametrize("role", ["anon", "authenticated"])
@pytest.mark.parametrize("table", sorted(EXPECTED_TABLES))
async def test_client_roles_have_no_privileges(engine: AsyncEngine, role: str, table: str) -> None:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        await connection.execute(text(f"SET LOCAL ROLE {role}"))
        with pytest.raises(ProgrammingError, match="permission denied"):
            # Table names come from the fixed EXPECTED_TABLES set, never from input.
            await connection.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))  # noqa: S608
        await transaction.rollback()


@pytest.mark.parametrize("role", ["anon", "authenticated"])
async def test_migration_bookkeeping_is_not_exposed(engine: AsyncEngine, role: str) -> None:
    """alembic_version exists before 0001 runs; 0004 locks it down like every other table."""
    async with engine.connect() as connection:
        transaction = await connection.begin()
        secured = await connection.scalar(
            text(
                "SELECT relrowsecurity FROM pg_class WHERE oid = 'public.alembic_version'::regclass"
            )
        )
        assert secured is True
        await connection.execute(text(f"SET LOCAL ROLE {role}"))
        with pytest.raises(ProgrammingError, match="permission denied"):
            await connection.execute(text("SELECT version_num FROM alembic_version"))
        await transaction.rollback()


async def test_rls_denies_rows_even_if_select_is_granted_by_mistake(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        await connection.execute(text("INSERT INTO companies (name) VALUES ('Empresa sintética')"))
        await connection.execute(text("GRANT SELECT ON companies TO authenticated"))
        await connection.execute(text("SET LOCAL ROLE authenticated"))
        visible = await connection.scalar(text("SELECT count(*) FROM companies"))
        await transaction.rollback()
    assert visible == 0


@pytest.mark.parametrize(
    "statement", ["UPDATE audit_logs SET outcome = 'DENIED'", "DELETE FROM audit_logs"]
)
async def test_audit_logs_are_append_only(engine: AsyncEngine, statement: str) -> None:
    async with engine.begin() as connection:
        await connection.execute(
            text("INSERT INTO audit_logs (action, outcome) VALUES ('LOGIN', 'SUCCESS')")
        )
    async with engine.connect() as connection:
        with pytest.raises(DBAPIError, match="append-only"):
            await connection.execute(text(statement))


async def test_published_checklist_cannot_change(engine: AsyncEngine) -> None:
    version_id = uuid4()
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO checklist_versions (id, version, label, status) "
                "VALUES (:id, 99, 'v99', 'DRAFT')"
            ),
            {"id": version_id},
        )
        await connection.execute(
            text(
                "INSERT INTO checklist_items (version_id, code, position, name, description, "
                "evaluation_question, expected_evidence, reference_status, keywords, priority, "
                "risk_level, effort) VALUES (:id, 'ISO-01', 1, 'n', 'd', 'q', 'e', 'draft', "
                "ARRAY['k'], 'LOW', 'LOW', 'LOW')"
            ),
            {"id": version_id},
        )
        await connection.execute(
            text("UPDATE checklist_versions SET status = 'PUBLISHED' WHERE id = :id"),
            {"id": version_id},
        )
    for statement in (
        "UPDATE checklist_items SET name = 'otro' WHERE version_id = :id",
        "DELETE FROM checklist_items WHERE version_id = :id",
        "UPDATE checklist_versions SET label = 'otro' WHERE id = :id",
    ):
        async with engine.connect() as connection:
            with pytest.raises(DBAPIError, match="immutable"):
                await connection.execute(text(statement), {"id": version_id})


async def test_user_email_is_unique_regardless_of_case(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.execute(text(INSERT_USER), {"id": uuid4(), "email": "A@x.test"})
        await connection.execute(text(INSERT_USER), {"id": uuid4(), "email": "b@x.test"})
    async with engine.connect() as connection:
        with pytest.raises(IntegrityError):
            await connection.execute(text(INSERT_USER), {"id": uuid4(), "email": "a@X.test"})


async def test_document_chunks_are_indexed_for_spanish_full_text_search(
    engine: AsyncEngine,
) -> None:
    async with engine.connect() as connection:
        indexdef = await connection.scalar(
            text(
                "SELECT indexdef FROM pg_indexes "
                "WHERE indexname = 'ix_document_chunks_search_vector'"
            )
        )
        generated = await connection.scalar(
            text(
                "SELECT pg_get_expr(d.adbin, d.adrelid) FROM pg_attrdef d "
                "JOIN pg_attribute a ON a.attrelid = d.adrelid AND a.attnum = d.adnum "
                "WHERE a.attrelid = 'document_chunks'::regclass AND a.attname = 'search_vector'"
            )
        )
    assert "gin" in indexdef.lower()
    assert "spanish" in generated
