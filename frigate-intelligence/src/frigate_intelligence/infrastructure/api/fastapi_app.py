from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from frigate_intelligence.config.dependencies import Container
from frigate_intelligence.interface_adapters.controllers.api_controller import (
    APIController,
)
from frigate_intelligence.infrastructure.api.routes.event_routes import (
    create_event_router,
)
from frigate_intelligence.infrastructure.api.routes.pos_routes import (
    create_pos_router,
)
from frigate_intelligence.infrastructure.api.routes.analytics_routes import (
    create_analytics_router,
)


def create_app(container: Container) -> FastAPI:
    app = FastAPI(
        title="Frigate Intelligence Platform",
        version="0.1.0",
        description="AI-powered Frigate NVR analytics API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://192.168.85.202:3000",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    controller = APIController(container.text_to_sql_use_case)
    app.include_router(controller.router)

    event_router = create_event_router(container.frigate_repo)
    app.include_router(event_router)

    pos_router = create_pos_router(container.correlate_pos_use_case)
    app.include_router(pos_router)

    analytics_router = create_analytics_router(container.analytics_use_case)
    app.include_router(analytics_router)

    return app
