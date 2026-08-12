"""Telephony provider interface.

A provider is responsible only for the *transport* of a phone call.
Conversation intelligence lives in the call engine + agent runtime.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from core.models import Call


class TelephonyProvider(ABC):
    name = "base"

    @abstractmethod
    def place_call(self, call: Call, callback_url: str | None = None) -> Call:
        """Dial the destination and attach it to the OS call webhooks."""

    @abstractmethod
    def hang_up(self, call: Call) -> Call:
        """End an in-progress call."""

    @abstractmethod
    def describe(self) -> dict:
        """Provider configuration summary for the OS status screen."""
