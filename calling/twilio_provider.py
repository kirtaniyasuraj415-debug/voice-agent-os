"""Twilio telephony provider - real PSTN phone calls.

The provider only dials. The OS REST API hosts the TwiML + speech webhooks
(see api/routes/calls_routes.py) that stream the voice agent conversation.
"""
from __future__ import annotations

import logging

from calling.base import TelephonyProvider
from core.config import settings
from core.models import Call

log = logging.getLogger("vaos.calling.twilio")


class TwilioProvider(TelephonyProvider):
    name = "twilio"

    def __init__(
        self,
        account_sid: str | None = None,
        auth_token: str | None = None,
        from_number: str | None = None,
        callback_base: str | None = None,
    ) -> None:
        self.account_sid = account_sid or settings.twilio_account_sid
        self.auth_token = auth_token or settings.twilio_auth_token
        self.from_number = from_number or settings.twilio_from_number
        self.callback_base = (callback_base or f"http://{settings.api_host}:{settings.api_port}").rstrip("/")
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Twilio credentials are required (TWILIO_ACCOUNT_SID/AUTH_TOKEN/FROM_NUMBER)")
        self._twilio = __import__("twilio.rest", fromlist=["Client"]).Client(
            self.account_sid, self.auth_token
        )

    def place_call(self, call: Call, callback_url: str | None = None) -> Call:
        twiml_url = callback_url or f"{self.callback_base}/api/v1/calls/{call.id}/twiml"
        self._twilio.calls.create(
            to=call.to_number,
            from_=self.from_number,
            url=twiml_url,
            method="POST",
            status_callback=f"{self.callback_base}/api/v1/calls/{call.id}/events",
        )
        call.provider = self.name
        return call

    def hang_up(self, call: Call) -> Call:
        from core.models import CallStatus

        try:
            twilio_call = self._twilio.calls.get(call.id).fetch()
            twilio_call.update(status="completed")
        except Exception:  # noqa: BLE001 - call may already be finished
            log.warning("hang_up: call %s not active on Twilio", call.id)
        call.status = CallStatus.COMPLETED
        return call

    def describe(self) -> dict:
        return {
            "provider": self.name,
            "from_number": self.from_number,
            "callback_base": self.callback_base,
        }


def build_twilio() -> TwilioProvider:
    return TwilioProvider()
