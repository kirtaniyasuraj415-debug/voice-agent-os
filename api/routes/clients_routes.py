"""Marketplace API - clients, subscriptions, usage, API keys."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.security import AdminDep, ClientDep
from core.models import Client, Subscription
from marketplace.tenant_manager import tenant_manager

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[Client], dependencies=[AdminDep])
def list_clients():
    return tenant_manager.list_clients()


@router.post("", response_model=Client, dependencies=[AdminDep])
def create_client(body: dict):
    return tenant_manager.create_client(
        name=body.get("name", "Unnamed"),
        email=body.get("email", "client@example.com"),
        plan=body.get("plan", "starter"),
    )


@router.get("/me", response_model=dict, dependencies=[ClientDep])
def me(client=ClientDep):
    return tenant_manager.usage_report(client.id)


@router.get("/{client_id}", response_model=Client, dependencies=[AdminDep])
def get_client(client_id: str):
    client = tenant_manager.get_client(client_id)
    if client is None:
        raise HTTPException(404, "client not found")
    return client


@router.post("/{client_id}/subscribe", response_model=Subscription, dependencies=[AdminDep])
def subscribe(client_id: str, body: dict):
    if tenant_manager.get_client(client_id) is None:
        raise HTTPException(404, "client not found")
    return tenant_manager.subscribe(client_id, body.get("product_id", ""))


@router.get("/{client_id}/usage", response_model=dict, dependencies=[AdminDep])
def usage(client_id: str):
    report = tenant_manager.usage_report(client_id)
    if not report:
        raise HTTPException(404, "client not found")
    return report
