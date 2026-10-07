"""ASGI application factory. Run with: uvicorn --factory auditor.main:create_app"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auditor.audit.api.router import router as audit_router
from auditor.companies.api.router import router as companies_router
from auditor.config import Settings, load_settings
from auditor.container import AppContainer
from auditor.documents.api.router import UPLOAD_PATH_PATTERN
from auditor.documents.api.router import router as documents_router
from auditor.evaluations.api.router import router as evaluations_router
from auditor.identity.api.router import router as identity_router
from auditor.identity.api.users_router import router as users_router
from auditor.shared.api.body_limit import BodySizeLimitMiddleware
from auditor.shared.api.dependencies import get_resolver
from auditor.shared.api.errors import register_error_handlers
from auditor.shared.api.health import build_health_router
from auditor.shared.api.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from auditor.shared.api.openapi import install_openapi
from auditor.shared.api.strict_query import reject_unknown_query_parameters
from auditor.shared.infrastructure.logging import configure_logging, get_logger

API_PREFIX = "/api/v1"
JSON_BODY_LIMIT = 256 * 1024

logger = get_logger(__name__)


def create_app(settings: Settings | None = None, container: AppContainer | None = None) -> FastAPI:
    settings = settings or load_settings()
    configure_logging(settings.log_level)
    container = container or AppContainer.build(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        logger.info("startup", app_env=settings.app_env, llm_provider=settings.llm_provider)
        yield
        await container.aclose()

    show_docs = settings.app_env.allows_dev_adapters
    app = FastAPI(
        title="Auditor Virtual API",
        description="Autoevaluación inicial de seguridad de la información.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if show_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if show_docs else None,
        dependencies=[Depends(reject_unknown_query_parameters)],
    )
    app.state.container = container
    app.dependency_overrides[get_resolver] = container.request_resolver

    register_error_handlers(app)
    app.include_router(build_health_router(container.is_ready))
    for router in (
        identity_router,
        users_router,
        companies_router,
        evaluations_router,
        documents_router,
        audit_router,
    ):
        app.include_router(router)
    install_openapi(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["authorization", "content-type", "x-request-id"],
        expose_headers=["x-request-id"],
        max_age=600,
    )
    app.add_middleware(
        SecurityHeadersMiddleware, enable_hsts=not settings.app_env.allows_dev_adapters
    )
    app.add_middleware(
        BodySizeLimitMiddleware,
        default_limit=JSON_BODY_LIMIT,
        upload_limit=settings.max_upload_bytes,
        upload_path=UPLOAD_PATH_PATTERN,
    )
    app.add_middleware(RequestIdMiddleware)
    return app
