"""Web Research Agent (inspired by 500-AI-Agents-Projects/agents/01)."""
from __future__ import annotations

from agents.base import BaseAgent
from nvidia.base import ChatMessage, LLMProvider

RESEARCHER_AGENT_DEF = {
    "id": "sys_researcher",
    "name": "Researcher",
    "system_prompt": (
        "You are a voice research assistant. Given a question, produce a concise "
        "3-5 point answer with key facts and one suggested follow-up question. "
        "If you cannot verify facts, say so clearly."
    ),
}


class ResearchAgent(BaseAgent):
    kind = "system"

    def __init__(self, agent_id: str, name: str, llm: LLMProvider) -> None:
        super().__init__(agent_id, name, llm=llm)
        self.system_prompt = RESEARCHER_AGENT_DEF["system_prompt"]

    def respond(self, user_text: str) -> str:
        return self.llm.chat(
            [ChatMessage("system", self.system_prompt), ChatMessage("user", user_text)]
        )
