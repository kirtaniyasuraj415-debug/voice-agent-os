"""Base agent class shared by every agent in the OS."""
from __future__ import annotations

from abc import ABC, abstractmethod

from nvidia.base import LLMProvider, TTSProvider
from nvidia.factory import nvidia_stack


class BaseAgent(ABC):
    """Minimal common contract: name, lifecycle, respond, speak."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        llm: LLMProvider | None = None,
        tts: TTSProvider | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.name = name
        self.llm = llm or nvidia_stack.llm
        self.tts = tts or nvidia_stack.tts
        self._running = False

    # ------------------------------------------------------------- metadata
    @property
    @abstractmethod
    def kind(self) -> str:
        """Agent category: 'voice', 'system', 'commander'."""

    # ----------------------------------------------------------- lifecycle
    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------ behavior
    @abstractmethod
    def respond(self, user_text: str) -> str:
        """Produce a reply for a single user utterance."""

    def speak(self, text: str) -> bytes:
        """Synthesize a reply into WAV audio bytes."""
        return self.tts.synthesize(text)

    def describe(self) -> dict:
        return {
            "id": self.agent_id,
            "name": self.name,
            "kind": self.kind,
            "running": self.is_running(),
        }
