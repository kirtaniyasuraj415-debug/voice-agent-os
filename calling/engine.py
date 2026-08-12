"""Call engine - orchestrates one phone conversation.

Sits between the telephony provider and the voice agent runtime:
    caller speaks -> transcript  -> agent brain -> reply -> TTS -> (provider plays it)
It also meters minutes for billing and publishes call events.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from core.events import bus
from core.models import Call, CallStatus
from storage.db import db

log = logging.getLogger("vaos.calling")


class CallEngine:
    def __init__(self) -> None:
        self._active: set[str] = set()

    # -------------------------------------------------------------- lifecycle
    def create_call(self, agent_id: str, to_number: str, tenant_id: str | None = None) -> Call:
        call = Call(agent_id=agent_id, to_number=to_number, tenant_id=tenant_id)
        db.save_call(call)
        bus.publish("call.created", {"call_id": call.id, "agent_id": agent_id, "to": to_number})
        return call

    def start(self, call: Call) -> Call:
        call.status = CallStatus.RINGING
        call.started_at = datetime.now(timezone.utc).isoformat()
        self._active.add(call.id)
        db.save_call(call)
        bus.publish("call.started", {"call_id": call.id})
        return call

    def add_turn(self, call: Call, speaker: str, text: str) -> Call:
        call.add_exchange(speaker, text)
        db.save_call(call)
        return call

    def complete(self, call: Call) -> Call:
        if call.started_at:
            try:
                started = datetime.fromisoformat(call.started_at)
                call.duration_seconds = int(time.time() - started.timestamp())
            except (ValueError, TypeError):
                call.duration_seconds = 0
        call.status = CallStatus.COMPLETED
        call.ended_at = datetime.now(timezone.utc).isoformat()
        self._active.discard(call.id)
        self._meter(call)
        db.save_call(call)
        bus.publish("call.completed", {"call_id": call.id, "duration": call.duration_seconds})
        return call

    def fail(self, call: Call, reason: str = "") -> Call:
        call.status = CallStatus.FAILED
        call.summary = reason or "call failed"
        call.ended_at = datetime.now(timezone.utc).isoformat()
        self._active.discard(call.id)
        db.save_call(call)
        bus.publish("call.failed", {"call_id": call.id, "reason": reason})
        return call

    def active_calls(self) -> int:
        return len(self._active)

    # -------------------------------------------------------------- simulation
    def run_simulated(self, call: Call, caller_script: list[str]) -> Call:
        """Drive a scripted caller through the agent brain (mock telephony)."""
        from agents.manager import agent_manager

        runtime = agent_manager.get_runtime(call.agent_id)
        self.start(call)
        call.status = CallStatus.IN_PROGRESS
        db.save_call(call)
        if runtime is None:
            return self.fail(call, "agent not active")

        for line in caller_script:
            self.add_turn(call, "caller", line)
            reply = runtime.respond(line)
            self.add_turn(call, "agent", reply)
            time.sleep(1.2)

        return self.complete(call)

    # --------------------------------------------------------------- billing
    @staticmethod
    def _meter(call: Call) -> None:
        """Charge completed minutes to the owning client's subscription."""
        from marketplace.tenant_manager import tenant_manager

        tenant_manager.meter_call(call)
