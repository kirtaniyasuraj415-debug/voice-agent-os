"""Shared domain models for the Voice Agent OS."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DISABLED = "disabled"


class CallStatus(str, Enum):
    QUEUED = "queued"
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VoiceAgent(BaseModel):
    """A voice agent instance - the product a client can buy/host."""

    id: str = Field(default_factory=lambda: f"ag_{uuid4hex()}")
    tenant_id: str | None = None
    name: str
    system_prompt: str
    voice: str = "English-US.Male"
    language: str = "en-US"
    status: AgentStatus = AgentStatus.DRAFT
    created_at: str = Field(default_factory=utcnow)
    updated_at: str = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Call(BaseModel):
    """A single outbound (or inbound) phone conversation."""

    id: str = Field(default_factory=lambda: f"call_{uuid4hex()}")
    tenant_id: str | None = None
    agent_id: str
    to_number: str
    direction: Literal["outbound", "inbound"] = "outbound"
    status: CallStatus = CallStatus.QUEUED
    provider: str = "mock"
    transcript: list[dict[str, str]] = Field(default_factory=list)
    recording_path: str | None = None
    created_at: str = Field(default_factory=utcnow)
    started_at: str | None = None
    ended_at: str | None = None
    duration_seconds: int = 0
    summary: str | None = None

    def add_exchange(self, speaker: str, text: str) -> None:
        self.transcript.append({"speaker": speaker, "text": text})

    def is_active(self) -> bool:
        return self.status in (CallStatus.QUEUED, CallStatus.RINGING, CallStatus.IN_PROGRESS)


class Client(BaseModel):
    """A paying client (tenant) of the voice-agent marketplace."""

    id: str = Field(default_factory=lambda: f"cli_{uuid4hex()}")
    name: str
    email: str
    api_key: str = Field(default_factory=lambda: f"vaos_{secrets_hex()}")
    plan: Literal["starter", "pro", "enterprise"] = "starter"
    monthly_minutes: int = 100
    created_at: str = Field(default_factory=utcnow)


class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: f"sub_{uuid4hex()}")
    client_id: str
    product_id: str
    status: Literal["active", "cancelled", "past_due"] = "active"
    minutes_used: int = 0
    created_at: str = Field(default_factory=utcnow)


def uuid4hex() -> str:
    import uuid

    return uuid.uuid4().hex[:12]


def secrets_hex() -> str:
    import secrets

    return secrets.token_hex(16)
