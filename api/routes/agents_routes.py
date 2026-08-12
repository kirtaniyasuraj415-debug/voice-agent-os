"""Agent management API."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException

from agents.manager import agent_manager
from api.security import AdminOrClientDep, require_admin
from core.models import AgentStatus, VoiceAgent
from marketplace.tenant_manager import tenant_manager
router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[VoiceAgent], dependencies=[AdminOrClientDep])
def list_agents(tenant_id: str | None = None, client=AdminOrClientDep):
    return agent_manager.list_agents(tenant_id if tenant_id else (client.id if client else None))


@router.post("", response_model=VoiceAgent, dependencies=[AdminOrClientDep])
def create_agent(body: dict, client=AdminOrClientDep):
    if client is None:
        target_tenant = body.get("tenant_id")
    else:
        target_tenant = body.get("tenant_id") or client.id
        if target_tenant == client.id and not tenant_manager.can_create_agent(client.id):
            raise HTTPException(429, "plan agent limit reached")
    record = agent_manager.create_agent(
        name=body.get("name", "Untitled"),
        system_prompt=body.get("system_prompt"),
        tenant_id=target_tenant,
        voice=body.get("voice", "English-US.Male"),
        language=body.get("language", "en-US"),
    )
    return record


@router.get("/{agent_id}", response_model=VoiceAgent, dependencies=[AdminOrClientDep])
def get_agent(agent_id: str):
    record = agent_manager.get_agent(agent_id)
    if record is None:
        raise HTTPException(404, "agent not found")
    return record


@router.post("/{agent_id}/activate", response_model=VoiceAgent)
def activate_agent(agent_id: str, _: Annotated[str, Header(alias="X-Admin-Key")] = ""):
    record = agent_manager.activate(agent_id)
    if record is None:
        raise HTTPException(404, "agent not found")
    return record


@router.post("/{agent_id}/deactivate", response_model=VoiceAgent)
def deactivate_agent(agent_id: str, _: Annotated[str, Header(alias="X-Admin-Key")] = ""):
    record = agent_manager.deactivate(agent_id)
    if record is None:
        raise HTTPException(404, "agent not found")
    return record


@router.post("/{agent_id}/start", response_model=dict)
def start_agent(agent_id: str, _: Annotated[str, Header(alias="X-Admin-Key")] = ""):
    runtime = agent_manager.start_voice_agent(agent_id)
    if runtime is None:
        raise HTTPException(404, "agent not found or not active")
    return runtime.describe()


@router.post("/{agent_id}/stop", response_model=dict)
def stop_agent(agent_id: str, _: Annotated[str, Header(alias="X-Admin-Key")] = ""):
    if not agent_manager.stop_voice_agent(agent_id):
        raise HTTPException(404, "agent not running")
    return {"ok": True}


@router.delete("/{agent_id}", status_code=204)
def delete_agent(agent_id: str, _: Annotated[str, Header(alias="X-Admin-Key")] = ""):
    if not agent_manager.delete_agent(agent_id):
        raise HTTPException(404, "agent not found")
