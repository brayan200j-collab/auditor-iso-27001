from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.documents.application.ports import NewDocument
from auditor.documents.domain.document import Document, DocumentStatus
from auditor.documents.infrastructure.models import DocumentModel


def _to_document(model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        company_id=model.company_id,
        evaluation_id=model.evaluation_id,
        analysis_run_id=model.analysis_run_id,
        original_name=model.original_name,
        storage_path=model.storage_path,
        size_bytes=model.size_bytes,
        sha256=model.sha256,
        page_count=model.page_count,
        has_text=model.has_text,
        status=DocumentStatus(model.status),
        uploaded_by=model.uploaded_by,
        created_at=model.created_at,
        extracted_at=model.extracted_at,
        purged_at=model.purged_at,
    )


class SqlDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, document: NewDocument) -> Document:
        model = DocumentModel(
            id=document.id,
            company_id=document.company_id,
            evaluation_id=document.evaluation_id,
            analysis_run_id=document.analysis_run_id,
            original_name=document.original_name,
            storage_path=document.storage_path,
            size_bytes=document.size_bytes,
            sha256=document.sha256,
            page_count=document.page_count,
            has_text=document.has_text,
            status=DocumentStatus.STORED,
            uploaded_by=document.uploaded_by,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_document(model)

    async def get(
        self, document_id: UUID, evaluation_id: UUID, company_id: UUID
    ) -> Document | None:
        model = await self._session.scalar(
            select(DocumentModel).where(
                DocumentModel.id == document_id,
                DocumentModel.evaluation_id == evaluation_id,
                DocumentModel.company_id == company_id,
            )
        )
        return _to_document(model) if model else None

    async def list_for_run(self, analysis_run_id: UUID, company_id: UUID) -> list[Document]:
        models = await self._session.scalars(
            select(DocumentModel)
            .where(
                DocumentModel.analysis_run_id == analysis_run_id,
                DocumentModel.company_id == company_id,
            )
            .order_by(DocumentModel.created_at)
        )
        return [_to_document(model) for model in models]

    async def count_for_run(self, analysis_run_id: UUID) -> int:
        count = await self._session.scalar(
            select(func.count()).where(DocumentModel.analysis_run_id == analysis_run_id)
        )
        return count or 0

    async def delete(self, document_id: UUID) -> None:
        await self._session.execute(delete(DocumentModel).where(DocumentModel.id == document_id))
