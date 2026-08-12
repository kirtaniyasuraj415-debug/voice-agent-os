"""System API - OS health, provider status, voice round-trip for testing."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from agents.manager import agent_manager
from calling.manager import call_manager
from core.registry import registry
from marketplace.tenant_manager import tenant_manager
from nvidia.factory import nvidia_stack
from voice.audio import audio_io

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
def system_status():
    return {
        "running_agents": registry.running_count(),
        "system_team": agent_manager.team_status(),
        "voice_agents": len(agent_manager.list_agents()),
        "clients": len(tenant_manager.list_clients()),
        "active_calls": call_manager.engine.active_calls(),
        "scheduled_calls": _scheduled_due(),
        "providers": nvidia_stack.enabled,
        "telephony": call_manager.describe(),
        "audio_mode": audio_io.mode,
    }


def _scheduled_due() -> int:
    from calling.scheduler import scheduler

    return scheduler.due_count()


@router.post("/voice/echo")
def voice_echo(body: dict):
    """One commander turn given text (voice testing without hardware)."""
    from voice.pipeline import pipeline

    reply, wav = pipeline.one_turn(text=body.get("text", ""))
    return {"reply": reply, "wav_bytes": len(wav)}


@router.get("/voice/tts")
def tts_audio(text: str = "Hello from the voice agent OS."):
    wav = nvidia_stack.tts.synthesize(text)
    return Response(wav, media_type="audio/wav")
