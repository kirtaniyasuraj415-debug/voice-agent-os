"""TTS providers: NVIDIA Riva cloud (gRPC) and offline mock."""
from __future__ import annotations

import io
import logging
import wave

from core.config import settings
from nvidia.base import TTSProvider

log = logging.getLogger("vaos.nvidia.tts")

# Public NVIDIA API catalog function for Riva TTS (see NVIDIA docs).
RIVA_TTS_FUNCTION_ID = "0149dedb-2be8-4195-b9a0-e57e0e14f972"


def _build_wav(pcm: bytes, sample_rate: int = 22050) -> bytes:
    """Wrap raw PCM bytes into a RIFF WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)
    return buf.getvalue()


class RivaTTS(TTSProvider):
    """Speech synthesis via NVIDIA Riva cloud (grpc.nvcf.nvidia.com)."""

    name = "nvidia"

    def __init__(
        self,
        api_key: str | None = None,
        uri: str = "grpc.nvcf.nvidia.com:443",
        function_id: str = RIVA_TTS_FUNCTION_ID,
        sample_rate: int = 22050,
    ) -> None:
        self.api_key = api_key or settings.nvidia_api_key
        self.sample_rate = sample_rate
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for RivaTTS")
        try:
            import riva.client
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "nvidia-riva-client is not installed. Run: pip install nvidia-riva-client"
            ) from exc

        auth = riva.client.Auth(
            uri=uri,
            use_ssl=True,
            metadata_args=[
                ["function-id", function_id],
                ["authorization", f"Bearer {self.api_key}"],
            ],
        )
        self._client = riva.client.SpeechSynthesisService(auth)

    def synthesize(self, text: str, voice: str = "English-US.Male") -> bytes:
        resp = self._client.synthesize(
            text,
            voice_name=voice or settings.nvidia_tts_voice,
            language_code="en-US",
            encoding=1,  # LINEAR_PCM
            sample_rate_hz=self.sample_rate,
        )
        return _build_wav(resp.audio, self.sample_rate)


class MockTTS(TTSProvider):
    """Offline fallback: produces a short beep-like WAV."""

    name = "mock"

    def __init__(self, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate

    def synthesize(self, text: str, voice: str = "English-US.Male") -> bytes:
        import numpy as np

        seconds = max(0.2, min(1.2, len(text) / 20.0))
        t = np.linspace(0, seconds, int(self.sample_rate * seconds), endpoint=False)
        tone = 0.5 * np.sin(2 * np.pi * 440 * t) * np.exp(-3 * t)
        pcm = (tone * 32767).astype(np.int16).tobytes()
        return _build_wav(pcm, self.sample_rate)
