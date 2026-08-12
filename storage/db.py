"""Persistence for the Voice Agent OS (SQLite)."""
from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

from core.config import settings
from core.models import AgentStatus, Call, CallStatus, Client, Subscription, VoiceAgent


class Database:
    """Thin, thread-safe SQLite wrapper using JSON columns for flexibility."""

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or settings.db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self.migrate()

    # ------------------------------------------------------------- schema
    def migrate(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY, tenant_id TEXT, name TEXT,
                    system_prompt TEXT, voice TEXT, language TEXT,
                    status TEXT, created_at TEXT, updated_at TEXT,
                    metadata TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS calls (
                    id TEXT PRIMARY KEY, tenant_id TEXT, agent_id TEXT,
                    to_number TEXT, direction TEXT, status TEXT,
                    provider TEXT, transcript TEXT, recording_path TEXT,
                    created_at TEXT, started_at TEXT, ended_at TEXT,
                    duration_seconds INTEGER, summary TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id TEXT PRIMARY KEY, name TEXT, email TEXT,
                    api_key TEXT UNIQUE, plan TEXT, monthly_minutes INTEGER,
                    created_at TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id TEXT PRIMARY KEY, client_id TEXT, product_id TEXT,
                    status TEXT, minutes_used INTEGER, created_at TEXT
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_agents_tenant ON agents(tenant_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_calls_agent ON calls(agent_id)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_calls_tenant ON calls(tenant_id)"
            )
            self._conn.commit()

    # ------------------------------------------------------------- agents
    def save_agent(self, agent: VoiceAgent) -> VoiceAgent:
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO agents
                (id, tenant_id, name, system_prompt, voice, language, status, created_at, updated_at, metadata)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    agent.id,
                    agent.tenant_id,
                    agent.name,
                    agent.system_prompt,
                    agent.voice,
                    agent.language,
                    agent.status.value,
                    agent.created_at,
                    agent.updated_at,
                    json.dumps(agent.metadata),
                ),
            )
            self._conn.commit()
        return agent

    def get_agent(self, agent_id: str) -> VoiceAgent | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM agents WHERE id = ?", (agent_id,)
            ).fetchone()
        return self._row_to_agent(row)

    def list_agents(self, tenant_id: str | None = None) -> list[VoiceAgent]:
        with self._lock:
            if tenant_id:
                rows = self._conn.execute(
                    "SELECT * FROM agents WHERE tenant_id = ? ORDER BY created_at DESC",
                    (tenant_id,),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM agents ORDER BY created_at DESC"
                ).fetchall()
        return [a for a in (self._row_to_agent(r) for r in rows) if a]

    def delete_agent(self, agent_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
            self._conn.commit()
        return cur.rowcount > 0

    @staticmethod
    def _row_to_agent(row: sqlite3.Row | None) -> VoiceAgent | None:
        if row is None:
            return None
        return VoiceAgent(
            id=row["id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            system_prompt=row["system_prompt"],
            voice=row["voice"],
            language=row["language"],
            status=AgentStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata"] or "{}"),
        )

    # --------------------------------------------------------------- calls
    def save_call(self, call: Call) -> Call:
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO calls
                (id, tenant_id, agent_id, to_number, direction, status, provider,
                 transcript, recording_path, created_at, started_at, ended_at,
                 duration_seconds, summary)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    call.id,
                    call.tenant_id,
                    call.agent_id,
                    call.to_number,
                    call.direction,
                    call.status.value,
                    call.provider,
                    json.dumps(call.transcript),
                    call.recording_path,
                    call.created_at,
                    call.started_at,
                    call.ended_at,
                    call.duration_seconds,
                    call.summary,
                ),
            )
            self._conn.commit()
        return call

    def get_call(self, call_id: str) -> Call | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM calls WHERE id = ?", (call_id,)
            ).fetchone()
        return self._row_to_call(row)

    def list_calls(
        self, tenant_id: str | None = None, agent_id: str | None = None, limit: int = 100
    ) -> list[Call]:
        query = "SELECT * FROM calls"
        clauses: list[str] = []
        params: list[str] = []
        if tenant_id:
            clauses.append("tenant_id = ?")
            params.append(tenant_id)
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(str(limit))
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [c for c in (self._row_to_call(r) for r in rows) if c]

    @staticmethod
    def _row_to_call(row: sqlite3.Row | None) -> Call | None:
        if row is None:
            return None
        return Call(
            id=row["id"],
            tenant_id=row["tenant_id"],
            agent_id=row["agent_id"],
            to_number=row["to_number"],
            direction=row["direction"],
            status=CallStatus(row["status"]),
            provider=row["provider"],
            transcript=json.loads(row["transcript"] or "[]"),
            recording_path=row["recording_path"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            duration_seconds=row["duration_seconds"],
            summary=row["summary"],
        )

    # ------------------------------------------------------------- clients
    def save_client(self, client: Client) -> Client:
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO clients
                (id, name, email, api_key, plan, monthly_minutes, created_at)
                VALUES (?,?,?,?,?,?,?)
                """,
                (
                    client.id,
                    client.name,
                    client.email,
                    client.api_key,
                    client.plan,
                    client.monthly_minutes,
                    client.created_at,
                ),
            )
            self._conn.commit()
        return client

    def get_client(self, client_id: str) -> Client | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM clients WHERE id = ?", (client_id,)
            ).fetchone()
        return self._row_to_client(row)

    def get_client_by_api_key(self, api_key: str) -> Client | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM clients WHERE api_key = ?", (api_key,)
            ).fetchone()
        return self._row_to_client(row)

    def list_clients(self) -> list[Client]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM clients ORDER BY created_at DESC"
            ).fetchall()
        return [c for c in (self._row_to_client(r) for r in rows) if c]

    @staticmethod
    def _row_to_client(row: sqlite3.Row | None) -> Client | None:
        if row is None:
            return None
        return Client(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            api_key=row["api_key"],
            plan=row["plan"],
            monthly_minutes=row["monthly_minutes"],
            created_at=row["created_at"],
        )

    # -------------------------------------------------------- subscriptions
    def save_subscription(self, sub: Subscription) -> Subscription:
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO subscriptions
                (id, client_id, product_id, status, minutes_used, created_at)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    sub.id,
                    sub.client_id,
                    sub.product_id,
                    sub.status,
                    sub.minutes_used,
                    sub.created_at,
                ),
            )
            self._conn.commit()
        return sub

    def list_subscriptions(self, client_id: str | None = None) -> list[Subscription]:
        query = "SELECT * FROM subscriptions"
        params: list[str] = []
        if client_id:
            query += " WHERE client_id = ?"
            params.append(client_id)
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [Subscription(**dict(r)) for r in rows]

    def close(self) -> None:
        with self._lock:
            self._conn.close()


db = Database()
