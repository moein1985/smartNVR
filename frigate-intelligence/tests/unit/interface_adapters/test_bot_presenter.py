from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLResponse,
)
from frigate_intelligence.domain.entities.query_result import QueryResult
from frigate_intelligence.interface_adapters.presenters.bot_presenter import (
    BotPresenter,
)


def test_to_markdown_success():
    response = TextToSQLResponse(
        question="Show events",
        sql="SELECT * FROM event",
        result=QueryResult(
            sql="SELECT * FROM event",
            columns=["id", "label"],
            rows=[("1", "person")],
            row_count=1,
        ),
        explanation="Found 1 person",
        attempts=1,
    )
    md = BotPresenter.to_markdown(response)
    assert "Show events" in md
    assert "SELECT * FROM event" in md
    assert "Found 1 person" in md
    assert "1 rows" in md


def test_to_markdown_error():
    response = TextToSQLResponse(
        question="test",
        sql="",
        result=QueryResult(
            sql="", columns=[], rows=[], row_count=0, error="DB error"
        ),
        explanation="Failed",
        attempts=3,
    )
    md = BotPresenter.to_markdown(response)
    assert "Error: DB error" in md


def test_to_alert():
    alert = BotPresenter.to_alert(
        {"label": "person", "camera": "cam1", "start_time": 1784386154.0}
    )
    assert "person" in alert
    assert "cam1" in alert
