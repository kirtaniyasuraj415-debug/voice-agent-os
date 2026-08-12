"""Provider interfaces for LLM / ASR / TTS."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

log = logging.getLogger("vaos.nvidia")


class ChatMessage:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content


class LLMProvider(ABC):
    """Text model provider (system prompt + conversation -> reply)."""

    name = "base"

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> str:
        """Return the assistant reply for a conversation."""


class ASRProvider(ABC):
    """Speech-to-text provider (audio bytes -> transcript)."""

    name = "base"

    @abstractmethod
    def transcribe(self, audio_bytes: bytes, language: str = "en-US") -> str:
        """Transcribe WAV audio bytes into text."""


class TTSProvider(ABC):
    """Text-to-speech provider (text -> wav audio bytes)."""

    name = "base"

    @abstractmethod
    def synthesize(self, text: str, voice: str = "English-US.Male") -> bytes:
        """Synthesize text into 16-bit mono PCM WAV bytes."""
