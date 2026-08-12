"""Scheduler - fires timed callbacks (outbound campaigns, reminders)."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from core.events import bus

SCHEDULER_INTERVAL = 5  # seconds


@dataclass(order=True)
class ScheduledCall:
    run_at: float
    agent_id: str
    to_number: str
    tenant_id: str | None = None
    call_id: str = field(default_factory=lambda: "")


class CallScheduler:
    def __init__(self, interval: int = SCHEDULER_INTERVAL) -> None:
        self._queue: list[ScheduledCall] = []
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._interval = interval

    def schedule(self, agent_id: str, to_number: str, when: datetime, tenant_id: str | None = None) -> str:
        item = ScheduledCall(
            run_at=when.timestamp(),
            agent_id=agent_id,
            to_number=to_number,
            tenant_id=tenant_id,
        )
        with self._lock:
            self._queue.append(item)
            self._queue.sort()
        return f"{item.agent_id}:{item.to_number}"

    def due_count(self) -> int:
        with self._lock:
            return sum(1 for q in self._queue if q.run_at <= time.time())

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="vaos-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _run(self) -> None:
        while not self._stop.is_set():
            now = time.time()
            due: list[ScheduledCall] = []
            with self._lock:
                still: list[ScheduledCall] = []
                for item in self._queue:
                    if item.run_at <= now:
                        due.append(item)
                    else:
                        still.append(item)
                self._queue = still
            for item in due:
                self._fire(item)
            self._stop.wait(self._interval)

    def _fire(self, item: ScheduledCall) -> None:
        from calling.engine import CallEngine
        from calling.manager import telephony

        engine = CallEngine()
        call = engine.create_call(item.agent_id, item.to_number, item.tenant_id)
        item.call_id = call.id
        bus.publish("call.scheduled.fire", {"call_id": call.id})
        telephony.place(call)


scheduler = CallScheduler()
