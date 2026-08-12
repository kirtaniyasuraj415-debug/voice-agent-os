"""Agent registry - the heartbeat of the agentic OS.

Every running agent (voice agents, the commander, system agents) is
registered here so any section can look it up by id or category.
"""
from __future__ import annotations

import threading
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid circular imports at runtime
    from agents.base import VoiceAgent

    # ruff: noqa: F401


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, "VoiceAgent"] = {}
        self._lock = threading.Lock()

    def register(self, agent: "VoiceAgent") -> None:
        with self._lock:
            self._agents[agent.agent_id] = agent

    def unregister(self, agent_id: str) -> bool:
        with self._lock:
            return self._agents.pop(agent_id, None) is not None

    def get(self, agent_id: str) -> "VoiceAgent | None":
        with self._lock:
            return self._agents.get(agent_id)

    def all(self) -> list["VoiceAgent"]:
        with self._lock:
            return list(self._agents.values())

    def by_kind(self, kind: str) -> list["VoiceAgent"]:
        with self._lock:
            return [a for a in self._agents.values() if a.kind == kind]

    def running_count(self) -> int:
        with self._lock:
            return sum(1 for a in self._agents.values() if a.is_running())

    def health_summary(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = defaultdict(int)
            for a in self._agents.values():
                counts[a.kind] += 1
        return dict(counts)


registry = AgentRegistry()
