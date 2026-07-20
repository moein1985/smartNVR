from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLResponse,
)
from frigate_intelligence.domain.entities.query_result import QueryResult
from frigate_intelligence.infrastructure.api.fastapi_app import create_app
from frigate_intelligence.config.dependencies import Container


def _create_mock_container() -> Container:
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = TextToSQLResponse(
        question="test",
        sql="SELECT * FROM event",
        result=QueryResult(
            sql="SELECT * FROM event",
            columns=["id", "label"],
            rows=[("1", "person")],
            row_count=1,
        ),
        explanation="Found 1 person event",
        attempts=1,
    )
    mock_repo = MagicMock()
    mock_repo.get_events.return_value = []

    return Container(
        frigate_repo=mock_repo,
        llm_service=MagicMock(),
        text_to_sql_use_case=mock_use_case,
        correlate_pos_use_case=MagicMock(),
        analytics_use_case=MagicMock(),
    )


def test_query_endpoint():
    container = _create_mock_container()
    app = create_app(container)
    client = TestClient(app)

    response = client.post(
        "/api/v1/query", json={"question": "Show me person events"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sql"] == "SELECT * FROM event"
    assert data["row_count"] == 1
    assert data["explanation"] == "Found 1 person event"
    assert data["columns"] == ["id", "label"]


def test_health_endpoint():
    container = _create_mock_container()
    app = create_app(container)
    client = TestClient(app)

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["db_connected"] is True


def test_events_endpoint():
    container = _create_mock_container()
    app = create_app(container)
    client = TestClient(app)

    response = client.get("/api/v1/events?camera=cam1&label=person")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["events"] == []


def test_query_with_retries():
    container = _create_mock_container()
    app = create_app(container)
    client = TestClient(app)

    response = client.post(
        "/api/v1/query",
        json={"question": "test question", "max_retries": 5},
    )
    assert response.status_code == 200
