"""Seed command.

    python -m auditor.seed checklist   # checklist v1 from seeds/checklist_v1.yaml (any environment)
    python -m auditor.seed users       # development users from SEED_* variables (local/test only)
    python -m auditor.seed             # both

Development users are created in Supabase Auth with the passwords given in the environment
(`make env` generates random ones). The command refuses to create them in pilot or production.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.checklist.application.import_checklist import ImportChecklist
from auditor.checklist.infrastructure.repository import SqlChecklistRepository
from auditor.checklist.infrastructure.yaml_loader import load_checklist_definition
from auditor.companies.infrastructure.models import CompanyModel
from auditor.config import SeedSettings, Settings, load_settings
from auditor.identity.infrastructure.models import CompanyUserModel, UserModel
from auditor.identity.infrastructure.supabase_admin import SupabaseAuthAdmin
from auditor.shared.domain.actor import Role
from auditor.shared.infrastructure.database import (
    SessionUnitOfWork,
    create_engine,
    create_session_factory,
)

CHECKLIST_FILE = "checklist_v1.yaml"
SYNTHETIC_COMPANIES = {
    "A": ("Empresa de prueba A S.A.S.", "900000001-1"),
    "B": ("Empresa de prueba B S.A.S.", "900000002-2"),
}


@dataclass(frozen=True, slots=True)
class DevUser:
    email: str
    password: str
    role: Role
    full_name: str
    company: str | None


def _out(message: str) -> None:
    sys.stdout.write(message + "\n")


def dev_users(seed: SeedSettings) -> list[DevUser]:
    candidates = [
        (seed.seed_admin_email, seed.seed_admin_password, Role.ADMIN, "Administración", None),
        (seed.seed_reviewer_email, seed.seed_reviewer_password, Role.REVIEWER, "Revisor", None),
        (seed.seed_sme_email, seed.seed_sme_password, Role.SME, "Usuario PYME A", "A"),
        (seed.seed_sme_b_email, seed.seed_sme_b_password, Role.SME, "Usuario PYME B", "B"),
        (seed.seed_mentor_email, seed.seed_mentor_password, Role.MENTOR, "Mentor", None),
    ]
    return [
        DevUser(email.strip().lower(), password.get_secret_value(), role, name, company)
        for email, password, role, name, company in candidates
        if email and password.get_secret_value()
    ]


async def seed_checklist(session: AsyncSession, settings: Settings) -> None:
    definition = load_checklist_definition(settings.seeds_dir / CHECKLIST_FILE)
    result = await ImportChecklist(
        SqlChecklistRepository(session), SessionUnitOfWork(session)
    ).execute(definition)
    state = "created" if result.created else "already present"
    _out(f"checklist v{result.version.version}: {len(result.version.items)} items ({state})")


async def _company_id(session: AsyncSession, key: str) -> UUID:
    name, tax_id = SYNTHETIC_COMPANIES[key]
    existing = await session.scalar(select(CompanyModel.id).where(CompanyModel.tax_id == tax_id))
    if existing:
        return existing
    company = CompanyModel(name=name, tax_id=tax_id, sector="Servicios", city="Cali")
    session.add(company)
    await session.flush()
    return company.id


async def seed_users(session: AsyncSession, settings: Settings) -> None:
    if not settings.app_env.allows_dev_adapters:
        raise SystemExit("Refusing to create development users outside local/test.")
    users = dev_users(SeedSettings())
    if not users:
        _out("no SEED_* users configured; skipping")
        return
    async with httpx.AsyncClient() as http:
        admin = SupabaseAuthAdmin(
            settings.supabase_url, settings.supabase_service_role_key.get_secret_value(), http
        )
        for user in users:
            user_id = await admin.find_user_id(user.email)
            if user_id is None:
                user_id = await admin.create_user(user.email, user.password)
            await session.execute(
                insert(UserModel)
                .values(id=user_id, email=user.email, full_name=user.full_name, role=user.role)
                .on_conflict_do_update(
                    index_elements=[UserModel.id],
                    set_={"role": user.role, "full_name": user.full_name, "active": True},
                )
            )
            if user.company:
                company_id = await _company_id(session, user.company)
                await session.execute(
                    insert(CompanyUserModel)
                    .values(company_id=company_id, user_id=user_id)
                    .on_conflict_do_nothing()
                )
            _out(f"user {user.role.value:<8} ready")
    await session.commit()


async def run(targets: set[str]) -> None:
    settings = load_settings()
    engine = create_engine(settings.database_url, use_null_pool=True)
    try:
        async with create_session_factory(engine)() as session:
            if "checklist" in targets:
                await seed_checklist(session, settings)
            if "users" in targets:
                await seed_users(session, settings)
    finally:
        await engine.dispose()


def main() -> None:
    targets = set(sys.argv[1:]) or {"checklist", "users"}
    unknown = targets - {"checklist", "users"}
    if unknown:
        raise SystemExit(f"Unknown seed target(s): {', '.join(sorted(unknown))}")
    asyncio.run(run(targets))


if __name__ == "__main__":
    main()
