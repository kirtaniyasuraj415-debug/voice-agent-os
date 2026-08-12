"""Tenant manager - the sell-to-clients layer of the OS.

A client (tenant) buys *voice agents* (products). Each client gets an
API key so they can drive their own agents through the public REST API.
"""
from __future__ import annotations

import logging

from core.events import bus
from core.models import Call, Client, Subscription
from storage.db import db

log = logging.getLogger("vaos.marketplace")

from marketplace.billing import PLAN_LIMITS, plan_limits  # noqa: E402


class TenantManager:
    def __init__(self) -> None:
        self._bootstrapped = False

    # ------------------------------------------------------------ clients
    def create_client(self, name: str, email: str, plan: str = "starter") -> Client:
        if plan not in PLAN_LIMITS:
            raise ValueError(f"unknown plan {plan!r} (use starter|pro|enterprise)")
        client = Client(name=name, email=email, plan=plan)
        client.monthly_minutes = plan_limits(plan)["monthly_minutes"]
        db.save_client(client)
        bus.publish("client.created", {"client_id": client.id, "name": client.name})
        return client

    def get_client(self, client_id: str) -> Client | None:
        return db.get_client(client_id)

    def client_by_api_key(self, api_key: str) -> Client | None:
        return db.get_client_by_api_key(api_key)

    def list_clients(self) -> list[Client]:
        return db.list_clients()

    # --------------------------------------------------------- subscriptions
    def subscribe(self, client_id: str, product_agent_id: str) -> Subscription:
        sub = Subscription(client_id=client_id, product_id=product_agent_id)
        db.save_subscription(sub)
        bus.publish("subscription.created", {"client_id": client_id, "product": product_agent_id})
        return sub

    def list_subscriptions(self, client_id: str) -> list[Subscription]:
        return db.list_subscriptions(client_id)

    def can_create_agent(self, client_id: str) -> bool:
        """Enforce the max-agents limit per plan."""
        client = db.get_client(client_id)
        if client is None:
            return False
        from agents.manager import agent_manager

        existing = len(agent_manager.list_agents(tenant_id=client_id))
        return existing < plan_limits(client.plan)["max_agents"]

    # --------------------------------------------------------------- metering
    def meter_call(self, call: Call) -> None:
        """Bill completed minutes to the tenant that owns the agent."""
        if not call.tenant_id or call.duration_seconds <= 0:
            return
        minutes = max(1, -(-call.duration_seconds // 60))
        client = db.get_client(call.tenant_id)
        if client is None:
            return
        subs = db.list_subscriptions(call.tenant_id)
        for sub in subs:
            if sub.product_id == call.agent_id:
                sub.minutes_used += minutes
                db.save_subscription(sub)
                break
        bus.publish("minutes.metered", {"client_id": call.tenant_id, "minutes": minutes})

    # -------------------------------------------------------------- summary
    def usage_report(self, client_id: str) -> dict:
        client = db.get_client(client_id)
        if client is None:
            return {}
        subs = db.list_subscriptions(client_id)
        total_minutes = sum(s.minutes_used for s in subs)
        limits = plan_limits(client.plan)
        return {
            "client": client.name,
            "plan": client.plan,
            "monthly_limit_minutes": client.monthly_minutes,
            "minutes_used": total_minutes,
            "minutes_left": max(0, client.monthly_minutes - total_minutes),
            "subscribed_agents": len(subs),
            "estimated_bill": round(total_minutes * limits["price_per_minute"], 2),
        }


tenant_manager = TenantManager()
