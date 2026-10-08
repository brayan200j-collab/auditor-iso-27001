"""Synthetic test data. Never real companies, people or documents."""

from __future__ import annotations

from itertools import count
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from auditor.companies.application.ports import CompanyData
from auditor.companies.infrastructure.repository import SqlCompanyRepository
from auditor.identity.application.ports import NewUser
from auditor.identity.domain.user import User
from auditor.identity.infrastructure.user_repository import SqlUserRepository
from auditor.shared.domain.actor import Role

_sequence = count(1)


async def create_company(session: AsyncSession, name: str | None = None) -> UUID:
    number = next(_sequence)
    company = await SqlCompanyRepository(session).add(
        CompanyData(
            name=name or f"Empresa sintética {number}",
            tax_id=f"800{number:06d}-1",
            sector="Servicios",
            city="Cali",
        )
    )
    await session.commit()
    return company.id


async def create_user(
    session: AsyncSession, role: Role, company_id: UUID | None = None, *, active: bool = True
) -> User:
    number = next(_sequence)
    repository = SqlUserRepository(session)
    user = await repository.add(
        NewUser(
            id=uuid4(),
            email=f"usuario{number}@example.test",
            full_name=f"Usuario {number}",
            role=role,
            company_id=company_id,
        )
    )
    if not active:
        user = await repository.update(user.id, active=False)
    await session.commit()
    return user


async def create_evaluation(
    session: AsyncSession,
    company_id: UUID,
    created_by: UUID,
    *,
    status: str = "DRAFT",
    reviewer_id: UUID | None = None,
    title: str = "Evaluación sintética",
) -> UUID:
    from auditor.evaluations.infrastructure.models import AnalysisRunModel, EvaluationModel

    evaluation = EvaluationModel(
        company_id=company_id,
        created_by=created_by,
        reviewer_id=reviewer_id,
        title=title,
        status=status,
    )
    session.add(evaluation)
    await session.flush()
    session.add(AnalysisRunModel(evaluation_id=evaluation.id, run_number=1))
    await session.commit()
    return evaluation.id


async def seed_checklist(session: AsyncSession) -> None:
    from pathlib import Path

    from auditor.checklist.application.import_checklist import ImportChecklist
    from auditor.checklist.infrastructure.repository import SqlChecklistRepository
    from auditor.checklist.infrastructure.yaml_loader import load_checklist_definition
    from auditor.shared.infrastructure.database import SessionUnitOfWork

    seed = Path(__file__).resolve().parents[4] / "seeds" / "checklist_v1.yaml"
    await ImportChecklist(SqlChecklistRepository(session), SessionUnitOfWork(session)).execute(
        load_checklist_definition(seed)
    )
