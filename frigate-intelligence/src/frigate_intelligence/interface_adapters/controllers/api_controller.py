from fastapi import APIRouter

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
        self.router.add_api_route("/health", self.health, methods=["GET"])

    async def query(self, request: QueryRequest) -> QueryResponse:
        req = TextToSQLRequest(
            question=request.question, max_retries=request.max_retries
        )
        response = self._use_case.execute(req)
        return APIPresenter.to_query_response(response)

    async def health(self) -> HealthResponse:
        return HealthResponse(
            status="ok", version="0.1.0", db_connected=True
        )
