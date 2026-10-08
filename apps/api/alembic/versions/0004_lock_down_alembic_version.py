"""lock down alembic_version and default privileges

`alembic_version` is created by Alembic before the first migration runs, so 0001 never revoked
it. On Supabase cloud new tables in `public` are granted to `anon` and `authenticated` by default,
which exposed this table through the Data API. This revision applies the same deny-by-default
rule to it and removes those default grants for every table and sequence created later by the
migration role.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-08 10:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON TABLE alembic_version FROM anon, authenticated")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated"
    )


def downgrade() -> None:
    # Privileges stay revoked on purpose: re-granting them would only re-open the exposure.
    op.execute("ALTER TABLE alembic_version DISABLE ROW LEVEL SECURITY")
