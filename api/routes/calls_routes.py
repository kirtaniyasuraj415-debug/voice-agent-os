"""Calls API - place calls, list calls, plus Twilio webhooks and NVIDIA TTS audio."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from api.security import AdminOrClientDep, ClientDep
from calling.manager import call_manager
from core.config import settings
from core.models import Call
from nvidia.factory import nvidia_stack

router = APIRouter(prefix="/calls", tags=["calls"])

CALLS_TAGS = ["calls"]


@router.get("", response_model=list[Call], dependencies=[AdminOrClientDep])
def list_calls(agent_id: str | None = None, limit: int = Query(50, le=200), client=AdminOrClientDep):
    return call_manager.list(
        tenant_id=(client.id if client else None),
        agent_id=agent_id,
        limit=limit,
    )


@router.post("", response_model=Call, dependencies=[AdminOrClientDep])
def place_call(body: dict, client=AdminOrClientDep):
    return call_manager.place(
        agent_id=body.get("agent_id", ""),
        to_number=body.get("to_number", ""),
        tenant_id=body.get("tenant_id") or (client.id if client else None),
    )


@router.get("/tts", include_in_schema=False)
def tts_audio(text: str = "Hello", voice: str | None = None):
    wav = nvidia_stack.tts.synthesize(text, voice or settings.nvidia_tts_voice)
    return Response(wav, media_type="audio/wav")


@router.get("/{call_id}", response_model=Call, dependencies=[AdminOrClientDep])
def get_call(call_id: str):
    call = call_manager.get(call_id)
    if call is None:
        raise HTTPException(404, "call not found")
    return call


@router.post("/{call_id}/hangup", response_model=Call)
def hang_up(call_id: str):
    call = call_manager.hang_up(call_id)
    if call is None:
        raise HTTPException(404, "call not found")
    return call


# ----------------------------------------------------------- Twilio webhooks
@router.post("/{call_id}/twiml", include_in_schema=False)
def twiml(call_id: str):
    xml = call_manager.twiml_greeting(call_id)
    return Response(xml, media_type="application/xml")


@router.post("/{call_id}/turn", include_in_schema=False)
def speech_turn(call_id: str, speech_result: str = "", from_=None):
    xml = call_manager.handle_speech(call_id, speech_result or None)
    return Response(xml, media_type="application/xml")


@router.post("/{call_id}/events", include_in_schema=False)
def call_events(call_id: str, call_status: str = ""):
    if call_status in ("completed", "failed"):
        call = call_manager.get(call_id)
        if call:
            call_manager.engine.complete(call)
    return Response("", status_code=200)


