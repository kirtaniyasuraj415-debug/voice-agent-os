"""LLM providers: NVIDIA NIM / AI Endpoints and offline mock."""
from __future__ import annotations

import logging

import httpx

from core.config import settings
from nvidia.base import ChatMessage, LLMProvider

log = logging.getLogger("vaos.nvidia.llm")


class NvidiaLLM(LLMProvider):
    """OpenAI-compatible NVIDIA NIM / AI Endpoints chat model."""

    name = "nvidia"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.nvidia_api_key
        self.base_url = (base_url or settings.nvidia_llm_base_url).rstrip("/")
        self.model = model or settings.nvidia_llm_model
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for NvidiaLLM")

    def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


class MockLLM(LLMProvider):
    """Deterministic offline fallback so the OS runs without a key."""

    name = "mock"

    def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> str:
        last = next((m for m in reversed(messages) if m.role in ("user", "human")), None)
        user_text = last.content if last else ""
        lowered = user_text.lower()

        if any(k in lowered for k in ("status", "hello", "hi ", "hey")):
            return "All systems are running normally. You can ask me to create an agent, make a call, or check reports."
        if any(k in lowered for k in ("create agent", "make an agent", "new agent")):
            return "Agent created successfully. Say 'call' to start a phone call with it."
        if any(k in lowered for k in ("call", "dial", "phone")):
            return "I will start the phone call now and read back the outcome."
        if any(k in lowered for k in ("agent", "list")):
            return "You currently have one active voice agent. Say 'status' for details."
        return (
            f"[mock-llm] I received: {user_text!r}. "
            "Add your NVIDIA_API_KEY to .env to enable real responses."
        )
