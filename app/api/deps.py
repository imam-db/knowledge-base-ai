from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException

from app.config import settings


def require_admin_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    expected = settings.admin_api_key
    if not expected or not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: invalid or missing API key",
        )
