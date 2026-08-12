"""Billing rules for the voice-agent marketplace."""
from __future__ import annotations

PLAN_LIMITS = {
    "starter": {"monthly_minutes": 100, "max_agents": 2, "price_per_minute": 0.05},
    "pro": {"monthly_minutes": 1000, "max_agents": 10, "price_per_minute": 0.03},
    "enterprise": {"monthly_minutes": 10000, "max_agents": 100, "price_per_minute": 0.02},
}


def plan_limits(plan: str) -> dict:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["starter"])


def price_for_minutes(plan: str, minutes: int) -> float:
    return round(minutes * plan_limits(plan)["price_per_minute"], 4)
