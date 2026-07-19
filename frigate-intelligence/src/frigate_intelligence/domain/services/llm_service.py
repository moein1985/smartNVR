from typing import Generator, Protocol


class LLMService(Protocol):
    def generate_sql(self, question: str, schema_context: str) -> str:
        """Convert a natural language question to a SQL query string."""
        ...

    def explain_result(self, question: str, sql: str, result_text: str) -> str:
        """Generate a natural language explanation of query results."""
        ...

    def explain_result_stream(
        self, question: str, sql: str, result_text: str
    ) -> Generator[str, None, None]:
        """Stream a natural language explanation token by token."""
        ...
