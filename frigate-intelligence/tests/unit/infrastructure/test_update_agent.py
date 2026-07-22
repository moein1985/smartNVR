"""Tests for Phase 15.1 Step 8: Update agent rollback mechanism."""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx

from frigate_intelligence.updater.agent import UpdateAgent, UpdateResult


def _make_mock_container(image_tag="frigate-intelligence:latest"):
    """Create a mock Docker container object."""
    container = MagicMock()
    container.image.tags = [image_tag]
    container.image.id = "sha256:abc123"
    return container


def _make_mock_client(image_tag="frigate-intelligence:latest"):
    """Create a mock Docker client with controllable behavior."""
    client = MagicMock()
    container = _make_mock_container(image_tag)
    client.containers.list.return_value = [container]

    mock_image = MagicMock()
    mock_image.tag.return_value = None
    client.images.get.return_value = mock_image

    loaded_image = MagicMock()
    loaded_image.tags = ["frigate-intelligence:v1.2.0"]
    loaded_image.id = "sha256:def456"
    client.images.load.return_value = [loaded_image]

    return client


def test_update_result_to_dict():
    """UpdateResult.to_dict should serialize all fields."""
    result = UpdateResult(
        status="success",
        message="Update applied",
        old_image="old:latest",
        new_image="new:v1.2",
        rollback_image="old:rollback",
        health_check_passed=True,
        details={"key": "value"},
    )
    d = result.to_dict()
    assert d["status"] == "success"
    assert d["old_image"] == "old:latest"
    assert d["new_image"] == "new:v1.2"
    assert d["rollback_image"] == "old:rollback"
    assert d["health_check_passed"] is True
    assert d["details"]["key"] == "value"


def test_agent_returns_failed_when_file_not_found():
    """Agent should return failed status when update file doesn't exist."""
    agent = UpdateAgent(
        update_file="/tmp/nonexistent_update_file.tar",
        container_name="frigate-intelligence",
    )
    result = agent.run()
    assert result["status"] == "failed"
    assert "not found" in result["message"]


def test_agent_successful_update():
    """Agent should complete a successful update when health check passes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        update_file = Path(tmpdir) / "update.tar"
        update_file.write_bytes(b"fake-tar-content")

        mock_client = _make_mock_client()

        with patch.object(UpdateAgent, "_get_docker_client", return_value=mock_client):
            with patch.object(UpdateAgent, "_wait_for_health", return_value=True):
                agent = UpdateAgent(
                    update_file=str(update_file),
                    container_name="frigate-intelligence",
                )
                result = agent.run()

    assert result["status"] == "success"
    assert result["health_check_passed"] is True
    assert result["old_image"] == "frigate-intelligence:latest"
    assert result["new_image"] == "frigate-intelligence:v1.2.0"
    assert result["rollback_image"] == "frigate-intelligence:rollback"

    mock_client.containers.list.assert_called()
    mock_client.images.load.assert_called_once()


def test_agent_rollback_on_health_check_failure():
    """Agent should rollback when health check fails after update."""
    with tempfile.TemporaryDirectory() as tmpdir:
        update_file = Path(tmpdir) / "update.tar"
        update_file.write_bytes(b"fake-tar-content")

        mock_client = _make_mock_client()

        with patch.object(UpdateAgent, "_get_docker_client", return_value=mock_client):
            with patch.object(UpdateAgent, "_wait_for_health", side_effect=[False, True]):
                agent = UpdateAgent(
                    update_file=str(update_file),
                    container_name="frigate-intelligence",
                )
                result = agent.run()

    assert result["status"] == "rolled_back"
    assert result["health_check_passed"] is True
    assert result["details"]["rollback_health"] is True
    assert "rolled back" in result["message"].lower()

    rollback_container = mock_client.containers.list.return_value[0]
    rollback_container.stop.assert_called_once()
    rollback_container.remove.assert_called_once_with(force=True)
    mock_client.containers.run.assert_called_once()


def test_agent_tags_rollback_before_loading_new_image():
    """Agent should tag :rollback before loading the new image."""
    with tempfile.TemporaryDirectory() as tmpdir:
        update_file = Path(tmpdir) / "update.tar"
        update_file.write_bytes(b"fake-tar-content")

        mock_client = _make_mock_client()

        with patch.object(UpdateAgent, "_get_docker_client", return_value=mock_client):
            with patch.object(UpdateAgent, "_wait_for_health", return_value=True):
                agent = UpdateAgent(
                    update_file=str(update_file),
                    container_name="frigate-intelligence",
                )
                agent.run()

    mock_client.images.get.assert_called_once_with("frigate-intelligence:latest")
    mock_image = mock_client.images.get.return_value
    mock_image.tag.assert_called_once_with("frigate-intelligence:rollback")


def test_agent_returns_failed_when_container_not_found():
    """Agent should return failed when the target container doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        update_file = Path(tmpdir) / "update.tar"
        update_file.write_bytes(b"fake-tar-content")

        mock_client = MagicMock()
        mock_client.containers.list.return_value = []

        with patch.object(UpdateAgent, "_get_docker_client", return_value=mock_client):
            agent = UpdateAgent(
                update_file=str(update_file),
                container_name="nonexistent-container",
            )
            result = agent.run()

    assert result["status"] == "failed"
    assert "not found" in result["message"]


def test_agent_returns_failed_when_docker_package_not_installed():
    """Agent should return failed when docker PyPI package is not available."""
    with tempfile.TemporaryDirectory() as tmpdir:
        update_file = Path(tmpdir) / "update.tar"
        update_file.write_bytes(b"fake-tar-content")

        with patch.object(UpdateAgent, "_get_docker_client", side_effect=ImportError("No module named 'docker'")):
            agent = UpdateAgent(
                update_file=str(update_file),
                container_name="frigate-intelligence",
            )
            result = agent.run()

    assert result["status"] == "failed"
    assert "docker" in result["message"].lower()


def test_wait_for_health_polls_until_success():
    """_wait_for_health should poll and return True when health endpoint responds ok."""
    agent = UpdateAgent(
        update_file="/tmp/fake.tar",
        container_name="frigate-intelligence",
    )

    call_count = 0

    def mock_get(url, timeout):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"status": "ok"}
            return resp
        raise httpx.ConnectError("Connection refused")

    with patch("frigate_intelligence.updater.agent.httpx") as mock_httpx:
        mock_httpx.get = mock_get
        mock_httpx.ConnectError = Exception

        with patch("frigate_intelligence.updater.agent.time.sleep"):
            with patch(
                "frigate_intelligence.updater.agent.time.time",
                side_effect=[0, 5, 10, 15, 20],
            ):
                result = agent._wait_for_health()

    assert result is True


def test_wait_for_health_times_out():
    """_wait_for_health should return False after timeout."""
    agent = UpdateAgent(
        update_file="/tmp/fake.tar",
        container_name="frigate-intelligence",
    )

    with patch("frigate_intelligence.updater.agent.httpx") as mock_httpx:
        mock_httpx.get.side_effect = Exception("Connection refused")
        mock_httpx.ConnectError = Exception

        with patch("frigate_intelligence.updater.agent.time.sleep"):
            with patch(
                "frigate_intelligence.updater.agent.time.time",
                side_effect=[0, 10, 20, 30, 40, 50, 61],
            ):
                result = agent._wait_for_health()

    assert result is False
