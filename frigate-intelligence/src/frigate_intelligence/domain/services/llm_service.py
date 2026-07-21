from typing import Generator, Protocol


class LLMService(Protocol):
    def generate_sql(self, question: str, schema_context: str) -> str:
        """Convert a natural language question to a SQL query string."""
        ...

    def classify_intent(self, question: str) -> dict:
        """Classify user intent as event_query or playback_query. Returns dict with intent, camera, start_time, end_time."""
        ...

    def smart_query(self, question: str, schema_context: str) -> dict:
        """Unified call: classify intent + generate SQL in one response. Returns dict with intent, sql, camera, start_time, end_time, explanation."""
        ...

    def explain_result(self, question: str, sql: str, result_text: str) -> str:
        """Generate a natural language explanation of query results."""
        ...

    def explain_result_stream(
        self, question: str, sql: str, result_text: str
    ) -> Generator[str, None, None]:
        """Stream a natural language explanation token by token."""
        ...
