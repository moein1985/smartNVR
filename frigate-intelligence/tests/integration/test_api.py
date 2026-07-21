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
        intent="event_query",
        playback_intent=None,
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
    assert "server_timestamp" in data
    assert "server_timezone" in data
    assert "server_datetime_iso" in data


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


def test_bug_023_health_endpoint_returns_timestamp():
    """Regression test for BUG-023: Health endpoint must return server timestamp and timezone info."""
    container = _create_mock_container()
    app = create_app(container)
    client = TestClient(app)

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["db_connected"] is True
    assert "server_timestamp" in data
    assert isinstance(data["server_timestamp"], (int, float))
    assert data["server_timestamp"] > 1_000_000_000
    assert "server_timezone" in data
    assert data["server_timezone"] == "UTC"
    assert "server_datetime_iso" in data
    assert "T" in data["server_datetime_iso"]
    assert "+" in data["server_datetime_iso"] or data["server_datetime_iso"].endswith("Z")


def test_bug_023_query_accepts_client_timezone():
    """Regression test for BUG-023: Query endpoint must accept client timezone fields and pass to use case."""
    container = _create_mock_container()
    app = create_app(container)
    client = TestClient(app)

    response = client.post(
        "/api/v1/query",
        json={
            "question": "What happened at 9am today?",
            "max_retries": 3,
            "client_timezone": "Asia/Tehran",
            "client_offset_minutes": 210,
            "client_timestamp": 1784394600.0,
        },
    )
    assert response.status_code == 200

    called_request = container.text_to_sql_use_case.execute.call_args[0][0]
    assert called_request.client_tz_info is not None
    assert called_request.client_tz_info["offset_minutes"] == 210
    assert called_request.client_tz_info["timezone"] == "Asia/Tehran"
    assert called_request.client_tz_info["timestamp"] == 1784394600.0


def test_bug_026_playback_intent_classification():
    """Regression test for BUG-026: Playback query should return intent='playback_query'
    with playback_intent populated and no SQL execution."""
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = TextToSQLResponse(
        question="Show video 9am to 9:30am on cam1",
        sql="",
        result=QueryResult(
            sql="",
            columns=[],
            rows=[],
            row_count=0,
        ),
        explanation="Opening playback for cam1 from 09:00 to 09:30.",
        attempts=1,
        intent="playback_query",
        playback_intent={
            "camera": "cam1",
            "start_time": 1784394000.0,
            "end_time": 1784395800.0,
            "date": "2026-07-21",
        },
    )
    mock_repo = MagicMock()
    container = Container(
        frigate_repo=mock_repo,
        llm_service=MagicMock(),
        text_to_sql_use_case=mock_use_case,
        correlate_pos_use_case=MagicMock(),
        analytics_use_case=MagicMock(),
    )
    app = create_app(container)
    client = TestClient(app)

    response = client.post(
        "/api/v1/query",
        json={"question": "Show video 9am to 9:30am on cam1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "playback_query"
    assert data["sql"] == ""
    assert data["row_count"] == 0
    assert data["playback_intent"] is not None
    assert data["playback_intent"]["camera"] == "cam1"
    assert data["playback_intent"]["start_time"] == 1784394000.0
    assert data["playback_intent"]["end_time"] == 1784395800.0
    assert data["playback_intent"]["date"] == "2026-07-21"


def test_bug_026_event_intent_still_works():
    """Regression test for BUG-026: Standard event query should return intent='event_query'
    with DB rows and no playback_intent."""
    mock_use_case = MagicMock()
    mock_use_case.execute.return_value = TextToSQLResponse(
        question="Was moein seen today?",
        sql="SELECT id, sub_label FROM event WHERE label='person' AND sub_label LIKE '%moein%'",
        result=QueryResult(
            sql="SELECT id, sub_label FROM event WHERE label='person' AND sub_label LIKE '%moein%'",
            columns=["id", "sub_label"],
            rows=[("123", "moein")],
            row_count=1,
        ),
        explanation="Yes, moein was seen today.",
        attempts=1,
        intent="event_query",
        playback_intent=None,
    )
    mock_repo = MagicMock()
    container = Container(
        frigate_repo=mock_repo,
        llm_service=MagicMock(),
        text_to_sql_use_case=mock_use_case,
        correlate_pos_use_case=MagicMock(),
        analytics_use_case=MagicMock(),
    )
    app = create_app(container)
    client = TestClient(app)

    response = client.post(
        "/api/v1/query",
        json={"question": "Was moein seen today?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "event_query"
    assert data["row_count"] == 1
    assert data["columns"] == ["id", "sub_label"]
    assert data["playback_intent"] is None
    assert "moein" in data["explanation"]
