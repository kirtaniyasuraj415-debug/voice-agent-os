"""Agent factory - builds runtime agents from stored VoiceAgent records."""
from __future__ import annotations

from agents.base import BaseAgent
from agents.runtime import VoiceAgentRuntime
from core.models import VoiceAgent


def build_voice_agent(record: VoiceAgent) -> VoiceAgentRuntime:
    """Instantiate a running brain from a persisted VoiceAgent record."""
    return VoiceAgentRuntime(
        agent_id=record.id,
        name=record.name,
        system_prompt=record.system_prompt,
        voice=record.voice,
        language=record.language,
    )


def is_base_agent(obj: object) -> bool:
    return isinstance(obj, BaseAgent)
