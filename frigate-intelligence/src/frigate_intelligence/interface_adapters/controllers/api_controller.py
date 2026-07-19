import json
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


class APIController:
    def __init__(self, text_to_sql_use_case: TextToSQLUseCase):
        self._use_case = text_to_sql_use_case
        self.router = APIRouter(prefix="/api/v1", tags=["intelligence"])
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route("/query", self.query, methods=["POST"])
        self.router.add_api_route("/query/stream", self.query_stream, methods=["POST"])
        self.router.add_api_route("/health", self.health, methods=["GET"])

    async def query(self, request: QueryRequest) -> QueryResponse:
        req = TextToSQLRequest(
            question=request.question, max_retries=request.max_retries
        )
        response = self._use_case.execute(req)
        return APIPresenter.to_query_response(response)

    async def query_stream(self, request: QueryRequest) -> StreamingResponse:
        req = TextToSQLRequest(
            question=request.question, max_retries=request.max_retries
        )
        result = self._use_case.execute_streaming(req)

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
