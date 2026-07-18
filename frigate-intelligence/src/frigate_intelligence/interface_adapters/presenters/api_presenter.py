from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLResponse,
)
from frigate_intelligence.interface_adapters.schemas.api_models import QueryResponse


class APIPresenter:
    @staticmethod
    def to_query_response(response: TextToSQLResponse) -> QueryResponse:
        return QueryResponse(
            question=response.question,
            sql=response.sql,
            columns=response.result.columns,
            rows=[list(r) for r in response.result.rows],
            row_count=response.result.row_count,
            explanation=response.explanation,
            attempts=response.attempts,
            error=response.result.error,
        )
