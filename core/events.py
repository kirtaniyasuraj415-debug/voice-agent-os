"""Minimal in-process event bus used by the agentic OS.

Publish-subscribe keeps every section decoupled: the voice pipeline,
the scheduler, the API and the agents all communicate through events.
"""
from __future__ import annotations

import threading
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable

Subscriber = Callable[[str, dict[str, Any]], None]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, fn: Subscriber) -> None:
        with self._lock:
            self._subscribers[event_type].append(fn)

    def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Publish an event synchronously to all subscribers."""
        event: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload or {},
        }
        with self._lock:
            targets = list(self._subscribers.get(event_type, []))
            targets += list(self._subscribers.get("*", []))
        for fn in targets:
            try:
                fn(event_type, event)
            except Exception:  # noqa: BLE001 - bus must never crash the system
                import logging

                logging.getLogger("vaos.bus").exception("subscriber failed")
        return event


bus = EventBus()
