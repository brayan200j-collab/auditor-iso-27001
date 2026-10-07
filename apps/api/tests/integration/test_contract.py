"""Property-based contract tests: every operation is exercised against its OpenAPI document."""

from __future__ import annotations

from typing import Any

import pytest
import schemathesis
from fastapi import FastAPI
from hypothesis import HealthCheck, settings
from schemathesis.checks import ignored_auth, positive_data_acceptance
from sqlalchemy.ext.asyncio import AsyncSession

from auditor.shared.domain.actor import Role
from tests.support.auth import auth_headers
from tests.support.factories import create_user


@pytest.fixture
def api_schema(app: FastAPI) -> Any:
    return schemathesis.openapi.from_asgi("/openapi.json", app)


@pytest.fixture
async def admin_token_headers(session: AsyncSession) -> dict[str, str]:
    admin = await create_user(session, Role.ADMIN)
    return auth_headers(admin.id)


schema = schemathesis.pytest.from_fixture("api_schema")


@schema.parametrize()
@settings(
    max_examples=15,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
def test_api_conforms_to_its_openapi_document(
    case: schemathesis.Case, admin_token_headers: dict[str, str]
) -> None:
    # Excluded checks (see docs/DECISIONS.md, D-019):
    # - ignored_auth re-sends our explicit Authorization header; anonymous access is covered by
    #   test_authentication_required.py.
    # - positive_data_acceptance treats business-rule rejections (e.g. an SME without a company)
    #   as failures; those rules cannot be expressed in JSON Schema.
    case.call_and_validate(
        headers=admin_token_headers, excluded_checks=[ignored_auth, positive_data_acceptance]
    )
