from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from auditor.shared.api.schemas import ApiModel


class HealthResponse(ApiModel):
    status: str


def build_health_router(readiness_check: Callable[[], Awaitable[bool]]) -> APIRouter:
    router = APIRouter(tags=["operations"])

    @router.get("/healthz", response_model=HealthResponse, summary="Liveness")
    async def healthz() -> HealthResponse:
        return HealthResponse(status="ok")

    @router.get(
        "/readyz",
        response_model=HealthResponse,
        summary="Readiness (database reachable)",
        responses={503: {"model": HealthResponse}},
    )
    async def readyz() -> HealthResponse | JSONResponse:
        try:
            ready = await readiness_check()
        except Exception:
            ready = False
        if not ready:
            return JSONResponse(status_code=503, content={"status": "unavailable"})
        return HealthResponse(status="ok")

    return router
