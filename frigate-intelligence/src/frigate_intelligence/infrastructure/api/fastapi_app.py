import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from frigate_intelligence.config.dependencies import Container
from frigate_intelligence.interface_adapters.controllers.api_controller import (
    APIController,
)
from frigate_intelligence.infrastructure.config.settings_manager import (
    SettingsManager,
)
from frigate_intelligence.infrastructure.scheduler.cron_service import CronService
from frigate_intelligence.infrastructure.api.routes.event_routes import (
    create_event_router,
)
from frigate_intelligence.infrastructure.api.routes.pos_routes import (
    create_pos_router,
)
from frigate_intelligence.infrastructure.api.routes.analytics_routes import (
    create_analytics_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)


def create_app(container: Container) -> FastAPI:
    settings_manager = SettingsManager()
    cron_service = CronService(settings_manager=settings_manager, container=container)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        cron_service.start()
        app.state.cron_service = cron_service
        app.state.settings_manager = settings_manager
        yield
        cron_service.stop()

    app = FastAPI(
        title="Frigate Intelligence Platform",
        version="0.1.0",
        description="AI-powered Frigate NVR analytics API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    controller = APIController(
        container.text_to_sql_use_case,
        settings_manager=settings_manager,
        frigate_repo=container.frigate_repo,
        cron_service=cron_service,
    )
    app.include_router(controller.router)

    event_router = create_event_router(container.frigate_repo)
    app.include_router(event_router)

    pos_router = create_pos_router(container.correlate_pos_use_case)
    app.include_router(pos_router)

    analytics_router = create_analytics_router(container.analytics_use_case)
    app.include_router(analytics_router)

    return app
