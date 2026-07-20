import json
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLUseCase,
    TextToSQLRequest,
)
from frigate_intelligence.interface_adapters.schemas.api_models import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
)
from frigate_intelligence.interface_adapters.presenters.api_presenter import (
    APIPresenter,
)
from frigate_intelligence.domain.models.settings_model import SettingsModel
from frigate_intelligence.infrastructure.config.settings_manager import (
    SettingsManager,
)

logger = logging.getLogger(__name__)


class APIController:
    def __init__(
        self,
        text_to_sql_use_case: TextToSQLUseCase,
        settings_manager: SettingsManager | None = None,
    ):
        self._use_case = text_to_sql_use_case
        self._settings_manager = settings_manager or SettingsManager()
        self.router = APIRouter(prefix="/api/v1", tags=["intelligence"])
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route("/query", self.query, methods=["POST"])
        self.router.add_api_route("/query/stream", self.query_stream, methods=["POST"])
        self.router.add_api_route("/health", self.health, methods=["GET"])
        self.router.add_api_route("/settings", self.get_settings, methods=["GET"])
        self.router.add_api_route("/settings", self.update_settings, methods=["POST"])

    async def query(self, request: QueryRequest) -> QueryResponse:
        logger.info(f"POST /query - question: {request.question}")
        req = TextToSQLRequest(
            question=request.question, max_retries=request.max_retries
        )
        response = self._use_case.execute(req)
        logger.info(f"POST /query - completed: {response.attempts} attempts, {response.result.row_count} rows")
        return APIPresenter.to_query_response(response)

    async def query_stream(self, request: QueryRequest) -> StreamingResponse:
        logger.info(f"POST /query/stream - question: {request.question}")
        req = TextToSQLRequest(
            question=request.question, max_retries=request.max_retries
        )
        result = self._use_case.execute_streaming(req)
        logger.info(f"POST /query/stream - SQL: {result.sql}, attempts: {result.attempts}, rows: {result.result.row_count}")

        def event_stream():
            meta = {
                "sql": result.sql,
                "columns": result.result.columns,
                "rows": [list(r) for r in result.result.rows],
                "row_count": result.result.row_count,
                "attempts": result.attempts,
                "error": result.result.error,
            }
            yield f"data: {json.dumps(meta)}\n\n"

            for chunk in result.explanation_stream:
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="ok", version="0.1.0", db_connected=True
        )

    async def get_settings(self) -> SettingsModel:
        logger.info("GET /settings")
        return self._settings_manager.load()

    async def update_settings(self, settings: SettingsModel) -> dict:
        logger.info("POST /settings")
        self._settings_manager.save(settings)
        return {"status": "ok", "message": "Settings saved successfully"}
