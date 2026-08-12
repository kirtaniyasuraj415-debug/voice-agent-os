"""Provider factory - picks LLM/ASR/TTS implementations from settings."""
from __future__ import annotations

import logging

from core.config import settings
from nvidia.asr import MockASR, RivaASR
from nvidia.base import ASRProvider, ChatMessage, LLMProvider, TTSProvider
from nvidia.llm import MockLLM, NvidiaLLM
from nvidia.tts import MockTTS, RivaTTS

log = logging.getLogger("vaos.nvidia.factory")


class ResilientLLM(LLMProvider):
    """Wraps the NVIDIA LLM: if it keeps failing (rate limits, downtime),
    degrade to the mock brain so the OS never dies mid-conversation."""

    name = "nvidia"

    def __init__(self, llm: NvidiaLLM) -> None:
        self.primary = llm
        self.fallback = MockLLM()
        self.downgraded = False

    def chat(self, messages: list[ChatMessage], temperature: float = 0.3, max_tokens: int = 512) -> str:
        try:
            reply = self.primary.chat(messages, temperature=temperature, max_tokens=max_tokens)
            self.downgraded = False
            return reply
        except Exception as exc:  # noqa: BLE001
            log.error("nvidia llm failed (%s); using mock fallback", exc)
            self.downgraded = True
            return self.fallback.chat(messages, temperature=temperature, max_tokens=max_tokens)


def build_llm() -> LLMProvider:
    if settings.provider_llm == "nvidia":
        if not settings.has_nvidia_key:
            log.warning("provider_llm=nvidia but NVIDIA_API_KEY is empty; falling back to mock")
            return MockLLM()
        return ResilientLLM(NvidiaLLM())
    return MockLLM()


def build_asr() -> ASRProvider:
    if settings.provider_asr == "nvidia":
        if not settings.has_nvidia_key:
            log.warning("provider_asr=nvidia but NVIDIA_API_KEY is empty; falling back to mock")
            return MockASR()
        return RivaASR()
    return MockASR()


def build_tts() -> TTSProvider:
    if settings.provider_tts == "nvidia":
        if not settings.has_nvidia_key:
            log.warning("provider_tts=nvidia but NVIDIA_API_KEY is empty; falling back to mock")
            return MockTTS()
        return RivaTTS()
    return MockTTS()


class NVIDIAStack:
    """The full NVIDIA integration bundle exposed to the OS."""

    def __init__(self) -> None:
        self.llm = build_llm()
        self.asr = build_asr()
        self.tts = build_tts()

    @property
    def enabled(self) -> dict[str, str]:
        return {
            "llm": self.llm.name,
            "asr": self.asr.name,
            "tts": self.tts.name,
        }

    def describe(self) -> str:
        return f"LLM={self.llm.name} ASR={self.asr.name} TTS={self.tts.name}"


nvidia_stack = NVIDIAStack()
