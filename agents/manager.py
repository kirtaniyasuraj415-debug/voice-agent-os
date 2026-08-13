"""Agent manager - lifecycle control for all voice agents in the OS."""
from __future__ import annotations

from core.events import bus
from core.models import AgentStatus, VoiceAgent
from core.registry import registry
from storage.db import db

from agents.catalog import AGENT_CLASSES, SYSTEM_TEAM, TEAM_NAMES
from agents.factory import build_voice_agent
from agents.runtime import VoiceAgentRuntime

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful voice assistant on a phone call. Keep replies short, "
    "friendly and conversational. Ask one question at a time."
)


class AgentManager:
    """Single entry point for everything agent-related."""

    def __init__(self) -> None:
        self._team: dict[str, object] = {}

    # ------------------------------------------------------------ voice agents
    def create_agent(
        self,
        name: str,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        tenant_id: str | None = None,
        voice: str = "English-US.Male",
        language: str = "en-US",
    ) -> VoiceAgent:
        record = VoiceAgent(
            name=name,
            system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
            tenant_id=tenant_id,
            voice=voice,
            language=language,
            status=AgentStatus.ACTIVE,
        )
        db.save_agent(record)
        bus.publish("agent.created", {"agent_id": record.id, "name": record.name})
        return record

    def activate(self, agent_id: str) -> VoiceAgent | None:
        record = db.get_agent(agent_id)
        if record is None:
            return None
        record.status = AgentStatus.ACTIVE
        db.save_agent(record)
        return record

    def deactivate(self, agent_id: str) -> VoiceAgent | None:
        record = db.get_agent(agent_id)
        if record is None:
            return None
        record.status = AgentStatus.DISABLED
        db.save_agent(record)
        self.stop_voice_agent(agent_id)
        return record

    def delete_agent(self, agent_id: str) -> bool:
        self.stop_voice_agent(agent_id)
        return db.delete_agent(agent_id)

    def list_agents(self, tenant_id: str | None = None) -> list[VoiceAgent]:
        return db.list_agents(tenant_id)

    def get_agent(self, agent_id: str) -> VoiceAgent | None:
        return db.get_agent(agent_id)

    # ------------------------------------------------------------- runtimes
    def start_voice_agent(self, agent_id: str) -> VoiceAgentRuntime | None:
        record = db.get_agent(agent_id)
        if record is None or record.status != AgentStatus.ACTIVE:
            return None
        if registry.get(agent_id):
            registry.get(agent_id).stop()
        runtime = build_voice_agent(record)
        runtime.start()
        registry.register(runtime)
        bus.publish("agent.started", {"agent_id": agent_id})
        return runtime

    def stop_voice_agent(self, agent_id: str) -> bool:
        runtime = registry.get(agent_id)
        if runtime is None:
            return False
        runtime.stop()
        registry.unregister(agent_id)
        bus.publish("agent.stopped", {"agent_id": agent_id})
        return True

    def get_runtime(self, agent_id: str) -> VoiceAgentRuntime | None:
        runtime = registry.get(agent_id)
        if runtime is not None:
            return runtime
        return self.start_voice_agent(agent_id)

    # ---------------------------------------------------------- system team
    def boot_team(self) -> None:
        """Start the built-in system team (from the 500-AI repo catalog)."""
        from nvidia.factory import nvidia_stack

        for key, definition in SYSTEM_TEAM.items():
            cls = AGENT_CLASSES[key]
            agent = cls(definition["id"], definition["name"], nvidia_stack.llm)
            agent.start()
            self._team[key] = agent
            registry.register(agent)  # type: ignore[arg-type]
        bus.publish("team.booted", {"team": TEAM_NAMES})
        self.ensure_demo_agents()

    def ensure_demo_agents(self) -> None:
        """Seed a few ready voice agents on serverless cold boots.

        Vercel instances get an ephemeral /tmp DB, so a freshly woken
        instance may have no agents yet. Guarantee callable ones always
        exist so the dashboard is useful on first open.
        """
        if db.list_agents():
            return
        demos = [
            ("sales", "You are a sales agent. Pitch the product in 2 short lines, then ask if they want a demo call."),
            ("support", "You are a support agent. Answer politely and resolve the customer issue in 2 short lines."),
            ("consultant", "You are a consultant. Give a crisp, useful answer and ask one follow-up question."),
        ]
        for name, prompt in demos:
            self.create_agent(name=name, system_prompt=prompt)
        for record in self.list_agents():
            self.start_voice_agent(record.id)

    def get_team_agent(self, key: str):
        return self._team.get(key)

    def team_status(self) -> dict[str, bool]:
        return {key: agent.is_running() for key, agent in self._team.items()}

    def team_names(self) -> str:
        return TEAM_NAMES


agent_manager = AgentManager()
