"""Tests for Phase 15.1 Steps 5-8: System routes (log viewer + OTA) and update agent."""
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def _app(tmp_path, monkeypatch) -> FastAPI:
    """Create a test app with system router pointing at temp log/update dirs."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "app.log"
    log_file.write_text(
        "line1: starting app\nline2: db connected\nline3: cron started\n",
        encoding="utf-8",
    )

    update_dir = tmp_path / "updates"
    update_dir.mkdir(parents=True)

    from frigate_intelligence.infrastructure.api.routes import system_routes

    monkeypatch.setattr(system_routes, "_LOG_FILE", log_file)
    monkeypatch.setattr(system_routes, "_UPDATE_DIR", update_dir)

    app = FastAPI()
    router = system_routes.create_system_router()
    app.include_router(router)
    return app


@pytest.fixture()
def _client(_app) -> TestClient:
    return TestClient(_app)


# --- Step 5: Log Viewer ---


def test_get_logs_returns_last_n_lines(_client):
    """GET /api/v1/system/logs should return the last N lines from the log file."""
    resp = _client.get("/api/v1/system/logs?lines=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert "line2: db connected" in data["lines"][0]
    assert "line3: cron started" in data["lines"][1]


def test_get_logs_default_100_lines(_client):
    """GET /api/v1/system/logs with no lines param should default to 100."""
    resp = _client.get("/api/v1/system/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3


def test_get_logs_file_not_found(tmp_path, monkeypatch):
    """Should return empty lines when log file doesn't exist."""
    from frigate_intelligence.infrastructure.api.routes import system_routes

    monkeypatch.setattr(system_routes, "_LOG_FILE", tmp_path / "nonexistent.log")
    monkeypatch.setattr(system_routes, "_UPDATE_DIR", tmp_path / "updates")

    app = FastAPI()
    app.include_router(system_routes.create_system_router())
    client = TestClient(app)

    resp = client.get("/api/v1/system/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["lines"] == []
    assert "not found" in data["message"]


def test_get_logs_rejects_invalid_line_count(_client):
    """Should reject lines=0 or lines > 1000."""
    resp = _client.get("/api/v1/system/logs?lines=0")
    assert resp.status_code == 422

    resp = _client.get("/api/v1/system/logs?lines=2000")
    assert resp.status_code == 422


# --- Steps 6-7: OTA Upload ---


def test_upload_update_rejects_non_tar_file(_client):
    """POST /api/v1/system/update should reject non-.tar files."""
    resp = _client.post(
        "/api/v1/system/update",
        files={"file": ("update.zip", b"fake content", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "tar" in resp.json()["detail"].lower()


def test_upload_update_rejects_empty_filename(_client):
    """Should reject upload with no filename (FastAPI returns 422 for empty multipart filename)."""
    resp = _client.post(
        "/api/v1/system/update",
        files={"file": ("", b"fake content", "application/octet-stream")},
    )
    assert resp.status_code in (400, 422)


def test_upload_update_saves_file_and_triggers_agent(_client, tmp_path):
    """POST /api/v1/system/update should save the .tar and trigger the update agent."""
    fake_tar_content = b"fake-tar-content-for-testing"

    mock_result = {
        "status": "success",
        "message": "Update applied successfully",
        "old_image": "frigate-intelligence:latest",
        "new_image": "frigate-intelligence:v1.2.0",
        "rollback_image": "frigate-intelligence:rollback",
        "health_check_passed": True,
        "details": {},
    }

    with patch(
        "frigate_intelligence.updater.agent.UpdateAgent"
    ) as MockAgent:
        mock_instance = MockAgent.return_value
        mock_instance.run.return_value = mock_result

        resp = _client.post(
            "/api/v1/system/update",
            files={"file": ("update_v1.2.0.tar", fake_tar_content, "application/octet-stream")},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"

    saved_file = tmp_path / "updates" / "update_v1.2.0.tar"
    assert saved_file.exists()
    assert saved_file.read_bytes() == fake_tar_content

    MockAgent.assert_called_once()
    mock_instance.run.assert_called_once()


def test_upload_update_handles_rollback_response(_client):
    """Should return rolled_back status when agent reports rollback."""
    fake_tar_content = b"fake-tar-content"

    mock_result = {
        "status": "rolled_back",
        "message": "Update rolled back due to health check failure",
        "health_check_passed": False,
        "details": {"rollback_health": True},
    }

    with patch(
        "frigate_intelligence.updater.agent.UpdateAgent"
    ) as MockAgent:
        MockAgent.return_value.run.return_value = mock_result

        resp = _client.post(
            "/api/v1/system/update",
            files={"file": ("bad_update.tar", fake_tar_content, "application/octet-stream")},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rolled_back"


def test_upload_update_handles_agent_failure(_client):
    """Should return 500 when the update agent raises an exception."""
    with patch(
        "frigate_intelligence.updater.agent.UpdateAgent"
    ) as MockAgent:
        MockAgent.return_value.run.side_effect = RuntimeError("Docker socket not accessible")

        resp = _client.post(
            "/api/v1/system/update",
            files={"file": ("update.tar", b"content", "application/octet-stream")},
        )

    assert resp.status_code == 500
    assert "Docker socket" in resp.json()["detail"]
