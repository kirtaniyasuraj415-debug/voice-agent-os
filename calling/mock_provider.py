"""Mock telephony provider - simulated calls for development and demos."""
from __future__ import annotations

import time

from calling.base import TelephonyProvider
from calling.engine import CallEngine
from core.models import Call, CallStatus

DEFAULT_SCRIPT = [
    "Hello, is this a good time to talk?",
    "Tell me more about your product.",
    "Okay, that sounds interesting. What is the price?",
    "Thanks, I will think about it.",
]


class MockProvider(TelephonyProvider):
    name = "mock"

    def __init__(self) -> None:
        self.engine = CallEngine()

    def place_call(self, call: Call, callback_url: str | None = None) -> Call:
        call.provider = self.name
        time.sleep(1)  # simulate ring time
        return self.engine.run_simulated(call, list(DEFAULT_SCRIPT))

    def hang_up(self, call: Call) -> Call:
        return self.engine.complete(call)

    def describe(self) -> dict:
        return {
            "provider": self.name,
            "mode": "simulated",
            "note": "set PROVIDER_TELEPHONY=twilio + Twilio credentials for real calls",
        }


def build_mock() -> MockProvider:
    return MockProvider()
