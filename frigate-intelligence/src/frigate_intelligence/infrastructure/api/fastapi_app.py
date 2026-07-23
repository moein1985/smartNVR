import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from frigate_intelligence.config.dependencies import Container
from frigate_intelligence.interface_adapters.controllers.api_controller import (
    APIController,
)
from frigate_intelligence.infrastructure.config.settings_manager import (
    SettingsManager,
)
from frigate_intelligence.infrastructure.config.report_rule_manager import (
    ReportRuleManager,
)
from frigate_intelligence.infrastructure.config.report_history_manager import (
    ReportHistoryManager,
)
from frigate_intelligence.infrastructure.logging_config import setup_logging
from frigate_intelligence.infrastructure.scheduler.report_scheduler import (
    ReportScheduler,
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
from frigate_intelligence.infrastructure.api.routes.system_routes import (
    create_system_router,
)
from frigate_intelligence.infrastructure.api.routes.auth_routes import (
    create_auth_router,
    create_user_router,
)
from frigate_intelligence.infrastructure.api.routes.report_rule_routes import (
    create_report_rule_router,
)

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} "
            f"-> {response.status_code} ({elapsed_ms:.1f}ms) [{correlation_id}]"
        )
        response.headers["X-Correlation-ID"] = correlation_id
        return response


def create_app(container: Container) -> FastAPI:
    settings_manager = SettingsManager()
    log_level = settings_manager.load().log_level
    setup_logging(level=log_level)
    logger.info("Initializing Frigate Intelligence Platform")

    rule_manager = ReportRuleManager()
    history_manager = ReportHistoryManager()
    report_scheduler = ReportScheduler(
        settings_manager=settings_manager,
        rule_manager=rule_manager,
        history_manager=history_manager,
        container=container,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        report_scheduler.start()
        app.state.report_scheduler = report_scheduler
        app.state.settings_manager = settings_manager
        app.state.rule_manager = rule_manager
        app.state.history_manager = history_manager
        yield
        report_scheduler.stop()

    app = FastAPI(
        title="Frigate Intelligence Platform",
        version="0.1.0",
        description="AI-powered Frigate NVR analytics API",
        lifespan=lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)
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
        cron_service=report_scheduler,
    )
    app.include_router(controller.router)

    event_router = create_event_router(container.frigate_repo)
    app.include_router(event_router)

    pos_router = create_pos_router(container.correlate_pos_use_case)
    app.include_router(pos_router)

    analytics_router = create_analytics_router(container.analytics_use_case)
    app.include_router(analytics_router)

    system_router = create_system_router()
    app.include_router(system_router)

    auth_router = create_auth_router()
    app.include_router(auth_router)

    user_router = create_user_router()
    app.include_router(user_router)

    report_rule_router = create_report_rule_router()
    app.include_router(report_rule_router)

    return app
