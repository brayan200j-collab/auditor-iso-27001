from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, Security, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auditor.documents.application.delete_document import DeleteDocument
from auditor.documents.application.get_document_link import GetDocumentLink
from auditor.documents.application.issue_upload_ticket import IssueUploadTicket
from auditor.documents.application.list_documents import ListDocuments
from auditor.documents.application.upload_document import IncomingFile, UploadDocument
from auditor.documents.domain.document import Document, DocumentStatus
from auditor.identity.public import ResolveTicketActor
from auditor.shared.api.dependencies import CurrentActor, Resolver, use_case
from auditor.shared.api.rate_limit import rate_limit
from auditor.shared.api.schemas import ERROR_RESPONSES, ApiModel
from auditor.shared.domain.actor import Actor

UPLOAD_PATH_PATTERN = r"^/api/v1/evaluations/[^/]+/documents$"

router = APIRouter(
    prefix="/api/v1/evaluations/{evaluation_id}/documents",
    tags=["documents"],
    responses={**ERROR_RESPONSES, 413: {"description": "Archivo demasiado grande"}},
)


_bearer = HTTPBearer(auto_error=False, description="Supabase access token (JWT)")


async def upload_actor(
    evaluation_id: UUID,
    resolver: Resolver,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer)],
    ticket: Annotated[
        str | None,
        Header(
            alias="X-Upload-Ticket", description="Ticket de carga temporal (alternativa al JWT)"
        ),
    ] = None,
) -> Actor:
    """Bearer token, or an upload ticket for this evaluation when the browser uploads directly."""
    token = credentials.credentials.strip() if credentials else ""
    if not token and ticket and ticket.strip():
        return await resolver.resolve(ResolveTicketActor).execute(ticket.strip(), evaluation_id)
    return await resolver.resolve_actor(token or None)


UploadActor = Annotated[Actor, Depends(upload_actor)]


class DocumentLinkResponse(ApiModel):
    url: str
    expires_in: int


class UploadTicketResponse(ApiModel):
    ticket: str
    expires_in: int


class DocumentResponse(ApiModel):
    """Metadata only: storage paths never leave the backend."""

    id: UUID
    original_name: str
    size_bytes: int
    page_count: int
    has_text: bool
    status: DocumentStatus
    created_at: datetime

    @classmethod
    def of(cls, document: Document) -> DocumentResponse:
        return cls(
            id=document.id,
            original_name=document.original_name,
            size_bytes=document.size_bytes,
            page_count=document.page_count,
            has_text=document.has_text,
            status=document.status,
            created_at=document.created_at,
        )


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit("upload"))],
    summary="Cargar un PDF (máximo 20 MB y 30 páginas, con texto seleccionable)",
)
async def upload_document(
    actor: UploadActor,
    evaluation_id: UUID,
    file: Annotated[UploadFile, File(description="Documento PDF")],
    upload: Annotated[UploadDocument, Depends(use_case(UploadDocument))],
) -> DocumentResponse:
    try:
        # The body-size middleware already capped what was received; read at most cap + 1.
        data = await file.read()
    finally:
        await file.close()
    document = await upload.execute(
        actor,
        evaluation_id,
        IncomingFile(filename=file.filename, content_type=file.content_type, data=data),
    )
    return DocumentResponse.of(document)


@router.get("", response_model=list[DocumentResponse], summary="Documentos de la evaluación")
async def list_documents(
    actor: CurrentActor,
    evaluation_id: UUID,
    list_use_case: Annotated[ListDocuments, Depends(use_case(ListDocuments))],
) -> list[DocumentResponse]:
    return [
        DocumentResponse.of(document)
        for document in await list_use_case.execute(actor, evaluation_id)
    ]


@router.delete(
    "/{document_id:uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un documento antes de iniciar el análisis",
)
async def delete_document(
    actor: CurrentActor,
    evaluation_id: UUID,
    document_id: UUID,
    delete: Annotated[DeleteDocument, Depends(use_case(DeleteDocument))],
) -> None:
    await delete.execute(actor, evaluation_id, document_id)


@router.post(
    "/upload-ticket",
    response_model=UploadTicketResponse,
    dependencies=[Depends(rate_limit("upload"))],
    summary="Ticket temporal para cargar un PDF directamente a la API",
)
async def upload_ticket(
    actor: CurrentActor,
    evaluation_id: UUID,
    issue: Annotated[IssueUploadTicket, Depends(use_case(IssueUploadTicket))],
) -> UploadTicketResponse:
    ticket = await issue.execute(actor, evaluation_id)
    return UploadTicketResponse(ticket=ticket.value, expires_in=ticket.expires_in)


@router.get(
    "/{document_id:uuid}/link",
    response_model=DocumentLinkResponse,
    dependencies=[Depends(rate_limit("download"))],
    summary="Enlace temporal para ver el PDF original (auditado)",
)
async def document_link(
    actor: CurrentActor,
    evaluation_id: UUID,
    document_id: UUID,
    get: Annotated[GetDocumentLink, Depends(use_case(GetDocumentLink))],
) -> DocumentLinkResponse:
    link = await get.execute(actor, evaluation_id, document_id)
    return DocumentLinkResponse(url=link.url, expires_in=link.expires_in)
