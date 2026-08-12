"""Central configuration loaded from environment / .env file."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- NVIDIA ----
    nvidia_api_key: str = ""

    # Provider selection (mock | nvidia | twilio | mic)
    provider_llm: str = "mock"
    provider_asr: str = "mock"
    provider_tts: str = "mock"
    provider_audio: str = "mock"
    provider_telephony: str = "mock"

    # NVIDIA endpoints
    nvidia_llm_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_llm_model: str = "meta/llama-3.3-70b-instruct"
    nvidia_riva_url: str = "https://riva.api.nvidia.com"
    nvidia_asr_language: str = "en-US"
    nvidia_tts_voice: str = "English-US.Male"

    # Voice assistant
    assistant_name: str = "Nova"
    assistant_wake_word: str = "nova"
    assistant_auto_grant: bool = True

    # Twilio telephony
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_admin_key: str = "change-me-admin-key"

    # Storage
    db_path: str = str(ROOT_DIR / "data" / "vaos.db")

    @property
    def has_nvidia_key(self) -> bool:
        return bool(self.nvidia_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
