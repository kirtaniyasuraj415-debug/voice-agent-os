"""API tests using FastAPI TestClient."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from api.server import app  # noqa: E402

client = TestClient(app)
ADMIN = {"X-Admin-Key": "change-me-admin-key"}


def test_root():
    assert client.get("/").status_code == 200


def test_admin_required():
    assert client.get("/api/v1/clients").status_code == 401


def test_client_creation_and_api_key_flow():
    r = client.post(
        "/api/v1/clients",
        headers=ADMIN,
        json={"name": "API Co", "email": "api@co.io", "plan": "pro"},
    )
    assert r.status_code == 200
    api_key = r.json()["api_key"]

    r2 = client.post(
        "/api/v1/agents",
        headers={"X-Api-Key": api_key},
        json={"name": "API Bot", "system_prompt": "You are a bot."},
    )
    assert r2.status_code == 200
    assert r2.json()["tenant_id"] == r.json()["id"]

    me = client.get("/api/v1/clients/me", headers={"X-Api-Key": api_key})
    assert me.status_code == 200
    assert me.json()["client"] == "API Co"


def test_agent_management():
    r = client.post(
        "/api/v1/assistant/command", json={"text": "create agent named Sales Agent"}
    )
    assert r.status_code == 200
    agent_id = r.json()["last_action"].split(":")[1]

    listed = client.get("/api/v1/agents", headers=ADMIN)
    assert any(a["id"] == agent_id for a in listed.json())

    start = client.post(f"/api/v1/agents/{agent_id}/start", headers=ADMIN)
    assert start.status_code == 200

    stop = client.post(f"/api/v1/agents/{agent_id}/stop", headers=ADMIN)
    assert stop.status_code == 200


def test_call_flow():
    r = client.post("/api/v1/assistant/command", json={"text": "create agent named CallBot"})
    agent_id = r.json()["last_action"].split(":")[1]
    c = client.post(
        "/api/v1/calls",
        headers=ADMIN,
        json={"agent_id": agent_id, "to_number": "+1555000"},
    )
    assert c.status_code == 200
    call = c.json()
    assert call["status"] in ("completed", "failed")
    assert len(call["transcript"]) > 0
