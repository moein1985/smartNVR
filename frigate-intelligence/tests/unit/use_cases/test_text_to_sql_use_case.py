from unittest.mock import MagicMock

from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLUseCase,
    TextToSQLRequest,
)
from frigate_intelligence.domain.entities.query_result import QueryResult


def test_successful_query():
    mock_repo = MagicMock()
    mock_repo.execute_sql.return_value = QueryResult(
        sql="SELECT * FROM event",
        columns=["id", "label"],
        rows=[("1", "person")],
        row_count=1,
    )
    mock_llm = MagicMock()
    mock_llm.generate_sql.return_value = "SELECT * FROM event"
    mock_llm.explain_result.return_value = "Found 1 person event"

    use_case = TextToSQLUseCase(mock_repo, mock_llm)
    response = use_case.execute(TextToSQLRequest(question="Show me events"))

    assert response.sql == "SELECT * FROM event"
    assert response.result.row_count == 1
    assert "1 person" in response.explanation
    assert response.attempts == 1


def test_retry_on_validation_failure():
    mock_repo = MagicMock()
    mock_llm = MagicMock()
    mock_llm.generate_sql.side_effect = ["DROP TABLE event", "SELECT * FROM event"]
    mock_llm.explain_result.return_value = "Results explained"
    mock_repo.execute_sql.return_value = QueryResult(
        sql="SELECT * FROM event",
        columns=["id"],
        rows=[],
        row_count=0,
    )

    use_case = TextToSQLUseCase(mock_repo, mock_llm)
    response = use_case.execute(TextToSQLRequest(question="Show events"))

    assert response.attempts == 2
    assert response.sql == "SELECT * FROM event"


def test_retry_on_execution_failure():
    mock_repo = MagicMock()
    mock_llm = MagicMock()
    mock_llm.generate_sql.side_effect = [
        "SELECT * FROM event WHERE nonexistent_col = 1",
        "SELECT * FROM event",
    ]
    mock_llm.explain_result.return_value = "Results explained"
    mock_repo.execute_sql.side_effect = [
        QueryResult(
            sql="SELECT * FROM event WHERE nonexistent_col = 1",
            columns=[],
            rows=[],
            row_count=0,
            error="no such column",
        ),
        QueryResult(
            sql="SELECT * FROM event",
            columns=["id"],
            rows=[("1",)],
            row_count=1,
        ),
    ]

    use_case = TextToSQLUseCase(mock_repo, mock_llm)
    response = use_case.execute(TextToSQLRequest(question="Show events"))

    assert response.attempts == 2
    assert response.result.is_success


def test_all_retries_exhausted():
    mock_repo = MagicMock()
    mock_llm = MagicMock()
    mock_llm.generate_sql.return_value = "DROP TABLE event"

    use_case = TextToSQLUseCase(mock_repo, mock_llm)
    response = use_case.execute(
        TextToSQLRequest(question="Show events", max_retries=2)
    )

    assert response.attempts == 2
    assert response.sql == ""
    assert "Failed" in response.explanation


def test_sql_extraction_from_markdown():
    mock_repo = MagicMock()
    mock_repo.execute_sql.return_value = QueryResult(
        sql="SELECT * FROM event",
        columns=["id"],
        rows=[("1",)],
        row_count=1,
    )
    mock_llm = MagicMock()
    mock_llm.generate_sql.return_value = "```sql\nSELECT * FROM event\n```"
    mock_llm.explain_result.return_value = "Result shown"

    use_case = TextToSQLUseCase(mock_repo, mock_llm)
    response = use_case.execute(TextToSQLRequest(question="Show events?"))

    assert response.sql == "SELECT * FROM event"
