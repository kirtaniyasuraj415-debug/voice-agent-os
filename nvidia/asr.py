"""ASR providers: NVIDIA Riva cloud (gRPC) and offline mock."""
from __future__ import annotations

import logging

from core.config import settings
from nvidia.base import ASRProvider

log = logging.getLogger("vaos.nvidia.asr")

# Public NVIDIA API catalog function for Riva ASR (see NVIDIA docs).
RIVA_ASR_FUNCTION_ID = "1598d209-5e27-4d3c-8079-4751568b1081"


class RivaASR(ASRProvider):
    """Speech recognition via NVIDIA Riva cloud (grpc.nvcf.nvidia.com)."""

    name = "nvidia"

    def __init__(
        self,
        api_key: str | None = None,
        uri: str = "grpc.nvcf.nvidia.com:443",
        function_id: str = RIVA_ASR_FUNCTION_ID,
    ) -> None:
        self.api_key = api_key or settings.nvidia_api_key
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for RivaASR")
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
        self._client = riva.client.ASRService(auth)

    def transcribe(self, audio_bytes: bytes, language: str = "en-US") -> str:
        import riva.client

        cfg = riva.client.RecognitionConfig(
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            sample_rate_hertz=16000,
            language_code=language or settings.nvidia_asr_language,
            max_alternatives=1,
            enable_automatic_punctuation=True,
        )
        resp = self._client.offline_recognize(audio_bytes, cfg)
        return " ".join(a.text for a in resp.results) or ""


class MockASR(ASRProvider):
    """Offline fallback: echoes the audio size so pipelines can run."""

    name = "mock"

    def transcribe(self, audio_bytes: bytes, language: str = "en-US") -> str:
        return f"[mock-asr: heard {len(audio_bytes)} bytes]"
