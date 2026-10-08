"""Supabase Auth (GoTrue) admin API adapter. Uses the service role key; never exposed to clients."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from auditor.shared.domain.errors import ConflictError, ProcessingError

_PAGE_SIZE = 200
_BAN_FOREVER = "876000h"


class SupabaseAuthAdmin:
    def __init__(self, base_url: str, service_role_key: str, http: httpx.AsyncClient) -> None:
        self._base = base_url.rstrip("/") + "/auth/v1"
        self._headers = {
            "apikey": service_role_key,
            "authorization": f"Bearer {service_role_key}",
        }
        self._http = http

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            return await self._http.request(
                method, f"{self._base}{path}", headers=self._headers, timeout=15.0, **kwargs
            )
        except httpx.HTTPError as exc:
            raise ProcessingError(
                detail=f"auth admin request failed: {type(exc).__name__}"
            ) from exc

    async def find_user_id(self, email: str) -> UUID | None:
        target = email.strip().lower()
        page = 1
        while True:
            response = await self._request(
                "GET", "/admin/users", params={"page": page, "per_page": _PAGE_SIZE}
            )
            _raise_for_status(response)
            users = response.json().get("users", [])
            for user in users:
                if str(user.get("email", "")).lower() == target:
                    return UUID(user["id"])
            if len(users) < _PAGE_SIZE:
                return None
            page += 1

    async def create_user(self, email: str, password: str) -> UUID:
        response = await self._request(
            "POST",
            "/admin/users",
            json={"email": email, "password": password, "email_confirm": True},
        )
        if response.status_code == httpx.codes.UNPROCESSABLE_ENTITY:
            raise ConflictError("Ya existe una cuenta con ese correo.")
        _raise_for_status(response)
        return UUID(response.json()["id"])

    async def invite_user(self, email: str, redirect_to: str | None) -> UUID:
        body: dict[str, Any] = {"email": email}
        params = {"redirect_to": redirect_to} if redirect_to else None
        response = await self._request("POST", "/invite", json=body, params=params)
        if response.status_code == httpx.codes.UNPROCESSABLE_ENTITY:
            raise ConflictError("Ya existe una cuenta con ese correo.")
        _raise_for_status(response)
        return UUID(response.json()["id"])

    async def set_banned(self, user_id: UUID, banned: bool) -> None:
        duration = _BAN_FOREVER if banned else "none"
        response = await self._request(
            "PUT", f"/admin/users/{user_id}", json={"ban_duration": duration}
        )
        _raise_for_status(response)

    async def delete_user(self, user_id: UUID) -> None:
        response = await self._request("DELETE", f"/admin/users/{user_id}")
        if response.status_code != httpx.codes.NOT_FOUND:
            _raise_for_status(response)


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    raise ProcessingError(detail=f"auth admin responded {response.status_code}")
