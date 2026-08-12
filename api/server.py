"""FastAPI application factory for the Voice Agent OS."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

from api.routes import (  # noqa: E402
    agents_router,
    calls_router,
    clients_router,
    system_router,
    voice_router,
)
from core.config import settings  # noqa: E402

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


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

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def dashboard():
        html = (WEB_DIR / "index.html").read_text(encoding="utf-8")
        return HTMLResponse(html)

    @app.get("/health", include_in_schema=False)
    def health():
        return {"status": "ok"}

    return app


app = create_app()
