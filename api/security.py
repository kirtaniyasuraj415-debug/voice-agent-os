"""Auth: admin key for the OS console, client API keys for the marketplace."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException

from core.config import settings
from marketplace.tenant_manager import tenant_manager


def require_admin(x_admin_key: Annotated[str, Header(alias="X-Admin-Key")] = "") -> None:
    if x_admin_key != settings.api_admin_key:
        raise HTTPException(status_code=401, detail="invalid admin key")


def require_client(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-Api-Key")] = None,
):
    key = x_api_key
    if not key and authorization and authorization.lower().startswith("bearer "):
        key = authorization.split(" ", 1)[1]
    client = tenant_manager.client_by_api_key(key) if key else None
    if client is None:
        raise HTTPException(status_code=401, detail="invalid client API key")
    return client


def admin_or_client(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-Api-Key")] = None,
    x_admin_key: Annotated[str, Header(alias="X-Admin-Key")] = "",
):
    """Allow either the OS admin or an authenticated client. Returns the client or None."""
    if x_admin_key == settings.api_admin_key:
        return None
    return require_client(authorization=authorization, x_api_key=x_api_key)


AdminDep = Depends(require_admin)
ClientDep = Depends(require_client)
AdminOrClientDep = Depends(admin_or_client)
