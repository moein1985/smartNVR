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


def test_bug_025_llm_model_upgrade_sql_generation():
    """Regression test for BUG-025: Upgraded LLM model (gemini-2.5-flash) should
    still generate valid SQL via generate_sql(). The new model supports JSON mode
    but generate_sql() must still return a plain SQL string."""
    mock_repo = MagicMock()
    mock_repo.execute_sql.return_value = QueryResult(
        sql="SELECT label, COUNT(*) FROM event GROUP BY label",
        columns=["label", "COUNT(*)"],
        rows=[("person", 5), ("car", 3)],
        row_count=2,
    )
    mock_llm = MagicMock()
    mock_llm.generate_sql.return_value = "SELECT label, COUNT(*) FROM event GROUP BY label"
    mock_llm.explain_result.return_value = "Found 2 labels"

    use_case = TextToSQLUseCase(mock_repo, mock_llm)
    response = use_case.execute(TextToSQLRequest(question="Count detections by label"))

    assert response.sql == "SELECT label, COUNT(*) FROM event GROUP BY label"
    assert response.result.row_count == 2
    assert response.attempts == 1
    mock_llm.generate_sql.assert_called_once()


def test_bug_025_enrich_question_removed():
    """Regression test for BUG-025: _enrich_question() should be removed.
    The question passed to the LLM must be the raw user question without
    injected hints. Verify by checking the LLM receives the exact question."""
    mock_repo = MagicMock()
    mock_repo.execute_sql.return_value = QueryResult(
        sql="SELECT * FROM event WHERE label='person'",
        columns=["id"],
        rows=[("1",)],
        row_count=1,
    )
    mock_llm = MagicMock()
    mock_llm.generate_sql.return_value = "SELECT * FROM event WHERE label='person'"
    mock_llm.explain_result.return_value = "Found 1 person"

    use_case = TextToSQLUseCase(mock_repo, mock_llm)
    raw_question = "Was moein seen today?"
    response = use_case.execute(TextToSQLRequest(question=raw_question))

    assert response.attempts == 1
    call_args = mock_llm.generate_sql.call_args
    user_msg = call_args[0][0]
    assert user_msg == raw_question
    assert "NOTE:" not in user_msg
    assert "sub_label LIKE" not in user_msg
    assert not hasattr(use_case, "_enrich_question")
