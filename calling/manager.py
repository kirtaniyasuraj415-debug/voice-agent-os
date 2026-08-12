"""Call manager - the public API of the calling section.

Chosen telephony provider is wired here; the rest of the OS never talks
to a concrete provider.
"""
from __future__ import annotations

import logging

from calling.base import TelephonyProvider
from calling.engine import CallEngine
from core.config import settings
from core.models import Call, CallStatus
from storage.db import db

log = logging.getLogger("vaos.calling")


class CallManager:
    def __init__(self) -> None:
        self.engine = CallEngine()
        self._provider: TelephonyProvider | None = None

    @property
    def provider(self) -> TelephonyProvider:
        if self._provider is None:
            self._provider = self._build_provider()
        return self._provider

    def _build_provider(self) -> TelephonyProvider:
        if settings.provider_telephony == "twilio":
            try:
                from calling.twilio_provider import TwilioProvider

                return TwilioProvider()
            except ValueError:
                log.warning("twilio selected but credentials missing; using mock")
        from calling.mock_provider import MockProvider

        return MockProvider()

    def place(self, agent_id: str, to_number: str, tenant_id: str | None = None) -> Call:
        call = self.engine.create_call(agent_id, to_number, tenant_id)
        return self.provider.place_call(call)

    def get(self, call_id: str) -> Call | None:
        return db.get_call(call_id)

    def list(self, tenant_id: str | None = None, agent_id: str | None = None, limit: int = 50) -> list[Call]:
        return db.list_calls(tenant_id, agent_id, limit)

    def hang_up(self, call_id: str) -> Call | None:
        call = db.get_call(call_id)
        if call is None:
            return None
        if call.is_active():
            return self.provider.hang_up(call)
        return call

    # --------------------------------------------------- Twilio webhooks
    def twiml_greeting(self, call_id: str) -> str:
        call = db.get_call(call_id)
        if call is None:
            return "<Response><Hangup/></Response>"
        self.engine.start(call)
        return self._twiml_turn(call, intro=True)

    def handle_speech(self, call_id: str, speech_result: str | None) -> str:
        call = db.get_call(call_id)
        if call is None:
            return "<Response><Hangup/></Response>"
        call.status = CallStatus.IN_PROGRESS
        db.save_call(call)

        from agents.manager import agent_manager

        runtime = agent_manager.get_runtime(call.agent_id)
        if runtime is None:
            self.engine.complete(call)
            return "<Response><Hangup/></Response>"

        if speech_result:
            self.engine.add_turn(call, "caller", speech_result)
            reply = runtime.respond(speech_result)
            self.engine.add_turn(call, "agent", reply)
        else:
            reply = "I did not catch that. Could you please repeat?"
        return self._twiml_turn(call, text=reply, intro=False)

    def _twiml_turn(self, call: Call, text: str | None = None, intro: bool = False) -> str:
        from core.config import settings

        base = f"http://{settings.api_host}:{settings.api_port}"
        tts_url = f"{base}/api/v1/tts?text={{text}}"
        turn_url = f"{base}/api/v1/calls/{call.id}/turn"
        if intro:
            from agents.manager import agent_manager

            runtime = agent_manager.get_runtime(call.agent_id)
            greeting = "Hello! This is a voice assistant call. Go ahead, please tell me how I can help."
            if runtime:
                greeting = runtime.respond("Hi, introduce yourself in one line.")
                self.engine.add_turn(call, "agent", greeting)
            text = greeting
        return (
            f'<Response><Gather input="speech" timeout="4" '
            f'action="{turn_url}" method="POST" speechTimeout="auto">'
            f'<Play>{tts_url.format(text=text)}</Play></Gather></Response>'
        )

    def describe(self) -> dict:
        return self.provider.describe()


call_manager = CallManager()
