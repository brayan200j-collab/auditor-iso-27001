from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query

from auditor.shared.domain.pagination import MAX_PAGE_SIZE, PageRequest


def page_params(
    page: Annotated[int, Query(ge=1, le=10_000, description="Página (desde 1)")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=MAX_PAGE_SIZE, description="Elementos por página")
    ] = 20,
) -> PageRequest:
    return PageRequest(page=page, page_size=page_size)


PageParams = Annotated[PageRequest, Depends(page_params)]
