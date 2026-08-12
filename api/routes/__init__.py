from api.routes.agents_routes import router as agents_router
from api.routes.calls_routes import router as calls_router
from api.routes.clients_routes import router as clients_router
from api.routes.system_routes import router as system_router
from api.routes.voice_routes import router as voice_router

__all__ = ["agents_router", "calls_router", "clients_router", "system_router", "voice_router"]
