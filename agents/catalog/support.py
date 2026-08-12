"""Customer Support Agent (inspired by 500-AI-Agents-Projects/agents/13).

Replaced the LangGraph RAG pipeline with the shared NVIDIA LLM plus an
escalation rule, keeping the same behaviour with far less code.
"""
from __future__ import annotations

from agents.base import BaseAgent
from nvidia.base import ChatMessage, LLMProvider

SUPPORT_AGENT_DEF = {
    "id": "sys_support",
    "name": "Support",
    "system_prompt": (
        "You are a friendly customer-support voice agent for CloudSync Pro. "
        "Answer from this knowledge base only: pricing Basic $9/mo (100GB, 2 devices), "
        "Pro $19/mo (1TB, 5 devices), Business $49/mo (5TB, unlimited). "
        "Cancellation is possible anytime with 14-day refunds. AES-256 encryption, "
        "SOC 2 Type II. If the customer is angry, mentions refund/lawsuit/data loss, "
        "escalate politely and give a case ID."
    ),
    "escalation_keywords": ["refund", "lawsuit", "furious", "fraud", "broken", "data loss"],
}


class SupportAgent(BaseAgent):
    kind = "system"

    def __init__(self, agent_id: str, name: str, llm: LLMProvider) -> None:
        super().__init__(agent_id, name, llm=llm)
        self.system_prompt = SUPPORT_AGENT_DEF["system_prompt"]

    def respond(self, user_text: str) -> str:
        text = user_text.lower()
        if any(k in text for k in SUPPORT_AGENT_DEF["escalation_keywords"]):
            case_id = f"#{abs(hash(user_text)) % 100000}"
            return f"I understand - connecting you to a senior specialist. Your case ID is {case_id}."
        reply = self.llm.chat(
            [ChatMessage("system", self.system_prompt), ChatMessage("user", user_text)]
        )
        return reply
