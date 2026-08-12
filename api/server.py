"""FastAPI application factory for the Voice Agent OS."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

from api.routes import (  # noqa: E402
    agents_router,
    calls_router,
    clients_router,
    system_router,
    voice_router,
)
from core.config import settings  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    from agents.manager import agent_manager
    from calling.scheduler import scheduler

    agent_manager.boot_team()
    scheduler.start()
    logging.getLogger("vaos.api").info("Voice Agent OS ready: %s", settings.assistant_name)
    yield
    scheduler.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Voice Agent OS",
        description="Agentic OS for voice agents: create agents, make calls, sell to clients.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(agents_router, prefix="/api/v1")
    app.include_router(calls_router, prefix="/api/v1")
    app.include_router(clients_router, prefix="/api/v1")
    app.include_router(system_router, prefix="/api/v1")
    app.include_router(voice_router, prefix="/api/v1")

    @app.get("/")
    def root():
        return {
            "name": "Voice Agent OS",
            "docs": "/docs",
            "endpoints": {
                "agents": "/api/v1/agents",
                "calls": "/api/v1/calls",
                "clients": "/api/v1/clients",
                "system": "/api/v1/system/status",
                "assistant": "/api/v1/assistant/command",
            },
        }

    return app


app = create_app()
