"""Voice assistant API - drive the commander programmatically."""
from __future__ import annotations

from fastapi import APIRouter

from voice.commander import commander

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/help")
def help_text():
    return {"commands": commander.respond("help")}


@router.post("/command")
def command(body: dict):
    """Send a spoken/text command to the OS commander, get a spoken reply."""
    text = body.get("text", "")
    reply = commander.respond(text)
    return {"command": text, "reply": reply, "last_action": commander.last_action}
