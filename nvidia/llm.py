"""LLM providers: NVIDIA NIM / AI Endpoints and offline mock.

Uses the OpenAI SDK pointed at NVIDIA's OpenAI-compatible endpoint
(https://integrate.api.nvidia.com/v1). Streaming + tool-friendly.
"""
from __future__ import annotations

import logging
import time

from openai import OpenAI

from core.config import settings
from nvidia.base import ChatMessage, LLMProvider

log = logging.getLogger("vaos.nvidia.llm")

MAX_RETRIES = 3
BACKOFF_SECONDS = 2.0


def _with_retry(fn, *, retries: int = MAX_RETRIES):
    """Retry transient failures (429 rate limits, 5xx) with backoff."""
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - need to inspect status
            last_error = exc
            status = getattr(exc, "status_code", None)
            if status in (429, 500, 502, 503, 504):
                wait = BACKOFF_SECONDS * (2**attempt)
                log.warning("nvidia llm transient error %s, retrying in %.1fs", status, wait)
                time.sleep(wait)
                continue
            raise
    raise last_error


class NvidiaLLM(LLMProvider):
    """Chat model served by NVIDIA NIM / AI Endpoints via the OpenAI SDK."""

    name = "nvidia"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key or settings.nvidia_api_key
        self.base_url = (base_url or settings.nvidia_llm_base_url).rstrip("/")
        self.model = model or settings.nvidia_llm_model
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for NvidiaLLM")
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=timeout)

    def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> str:
        payload = [{"role": m.role, "content": m.content} for m in messages]

        def _call() -> str:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=payload,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return (resp.choices[0].message.content or "").strip()

        return _with_retry(_call)

    def chat_stream(self, messages: list[ChatMessage], max_tokens: int = 512):
        """Yield reply text chunks as they arrive (low latency voice)."""
        payload = [{"role": m.role, "content": m.content} for m in messages]
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=payload,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            if not getattr(chunk, "choices", None):
                continue
            if len(chunk.choices) == 0 or getattr(chunk.choices[0], "delta", None) is None:
                continue
            content = getattr(chunk.choices[0].delta, "content", None)
            if content:
                yield content


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
