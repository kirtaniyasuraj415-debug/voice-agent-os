"""End-to-end tests for the Voice Agent OS core flows."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.manager import agent_manager  # noqa: E402
from calling.manager import call_manager  # noqa: E402
from marketplace.tenant_manager import tenant_manager  # noqa: E402
from voice.commander import commander  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def boot():
    agent_manager.boot_team()


def test_commander_creates_agent():
    reply = commander.respond("create agent named sales")
    assert "created" in reply.lower()
    agents = agent_manager.list_agents()
    assert any(a.name == "Sales" for a in agents)


def test_commander_status():
    reply = commander.respond("how are you")
    assert "providers" in reply.lower() or "status" in reply.lower()


def test_commander_list_agents():
    reply = commander.respond("list agents")
    assert "voice agents" in reply


def test_client_lifecycle_and_limits():
    client = tenant_manager.create_client("Acme", "a@acme.com", plan="starter")
    assert client.api_key.startswith("vaos_")
    assert tenant_manager.client_by_api_key(client.api_key).id == client.id

    starter = tenant_manager.get_client(client.id)
    assert starter.monthly_minutes == 100


def test_plan_limit_enforced():
    client = tenant_manager.create_client("Small", "s@small.com", plan="starter")
    for i in range(2):
        agent_manager.create_agent(name=f"Bot{i}", tenant_id=client.id)
    assert not tenant_manager.can_create_agent(client.id)


def test_voice_agent_call():
    record = agent_manager.create_agent(name="CallBot")
    call = call_manager.place(record.id, "+1555000", tenant_id=None)
    assert call.status.value in ("completed", "failed")
    assert call.duration_seconds >= 0


def test_subscription_metering():
    client = tenant_manager.create_client("Big", "b@big.com", plan="pro")
    record = agent_manager.create_agent(name="MeterBot")
    tenant_manager.subscribe(client.id, record.id)
    call = call_manager.place(record.id, "+1555001", tenant_id=client.id)
    report = tenant_manager.usage_report(client.id)
    assert report["minutes_used"] >= 1
    assert report["estimated_bill"] > 0


def test_team_booted():
    team = agent_manager.team_status()
    assert team.get("support") is True
    assert team.get("researcher") is True
    assert team.get("summarizer") is True
