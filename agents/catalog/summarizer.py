"""News Summarizer Agent (inspired by 500-AI-Agents-Projects/agents/06)."""
from __future__ import annotations

from agents.base import BaseAgent
from nvidia.base import ChatMessage, LLMProvider

SUMMARIZER_AGENT_DEF = {
    "id": "sys_summarizer",
    "name": "Summarizer",
    "system_prompt": (
        "You summarize text for a spoken briefing. Keep it to 3 bullet points, "
        "plain language, maximum 40 words, ending with one action item if relevant."
    ),
}


class SummarizerAgent(BaseAgent):
    kind = "system"

    def __init__(self, agent_id: str, name: str, llm: LLMProvider) -> None:
        super().__init__(agent_id, name, llm=llm)
        self.system_prompt = SUMMARIZER_AGENT_DEF["system_prompt"]

    def respond(self, user_text: str) -> str:
        return self.llm.chat(
            [ChatMessage("system", self.system_prompt), ChatMessage("user", user_text)]
        )
