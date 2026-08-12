"""Voice agent runtime - a deployable, sellable phone agent."""
from __future__ import annotations

from agents.base import BaseAgent
from nvidia.base import LLMProvider, TTSProvider


class VoiceAgentRuntime(BaseAgent):
    """Runs one VoiceAgent record: system prompt + LLM = conversation brain."""

    kind = "voice"

    def __init__(
        self,
        agent_id: str,
        name: str,
        system_prompt: str,
        voice: str = "English-US.Male",
        language: str = "en-US",
        llm: LLMProvider | None = None,
        tts: TTSProvider | None = None,
    ) -> None:
        super().__init__(agent_id, name, llm=llm, tts=tts)
        self.system_prompt = system_prompt
        self.voice = voice
        self.language = language
        self.history: list[dict[str, str]] = []

    def respond(self, user_text: str) -> str:
        from nvidia.base import ChatMessage

        self.history.append({"role": "user", "content": user_text})
        messages = [ChatMessage("system", self.system_prompt)]
        messages += [ChatMessage(m["role"], m["content"]) for m in self.history[-10:]]
        reply = self.llm.chat(messages)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def reset_history(self) -> None:
        self.history = []

    def describe(self) -> dict:
        data = super().describe()
        data["voice"] = self.voice
        data["language"] = self.language
        data["history_len"] = len(self.history)
        return data
