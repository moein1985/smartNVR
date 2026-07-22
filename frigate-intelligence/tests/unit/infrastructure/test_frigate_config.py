"""Tests for FrigateConfigService and frigate-config endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from frigate_intelligence.infrastructure.config.frigate_config_service import (
    FrigateConfigService,
    _deep_merge,
)
from frigate_intelligence.infrastructure.api.routes import system_routes


# ─── FrigateConfigService unit tests ───


def test_frigate_config_read_existing(tmp_path):
    """read() should parse an existing frigate.yml."""
    config_file = tmp_path / "frigate.yml"
    config_file.write_text("mqtt:\n  host: localhost\n  port: 1883\n", encoding="utf-8")
    service = FrigateConfigService(config_path=config_file)
    config = service.read()
    assert config["mqtt"]["host"] == "localhost"
    assert config["mqtt"]["port"] == 1883


def test_frigate_config_read_missing_file(tmp_path):
    """read() should return empty dict when file doesn't exist."""
    service = FrigateConfigService(config_path=tmp_path / "nonexistent.yml")
    assert service.read() == {}


def test_frigate_config_update_partial(tmp_path):
    """update() should deep-merge partial updates into existing config."""
    config_file = tmp_path / "frigate.yml"
    config_file.write_text(
        "mqtt:\n  host: localhost\n  port: 1883\ncameras:\n  cam1:\n    enabled: true\n",
        encoding="utf-8",
    )
    service = FrigateConfigService(config_path=config_file)
    merged = service.update({"mqtt": {"port": 1884}})

    assert merged["mqtt"]["host"] == "localhost"
    assert merged["mqtt"]["port"] == 1884
    assert merged["cameras"]["cam1"]["enabled"] is True

    reread = service.read()
    assert reread["mqtt"]["port"] == 1884


def test_frigate_config_update_new_key(tmp_path):
    """update() should add new top-level keys."""
    config_file = tmp_path / "frigate.yml"
    config_file.write_text("mqtt:\n  host: localhost\n", encoding="utf-8")
    service = FrigateConfigService(config_path=config_file)
    merged = service.update({"detect": {"enabled": True}})
    assert merged["detect"]["enabled"] is True
    assert merged["mqtt"]["host"] == "localhost"


def test_deep_merge_basic():
    """_deep_merge should recursively merge nested dicts."""
    base = {"a": {"b": 1, "c": 2}, "d": 3}
    override = {"a": {"b": 10}}
    result = _deep_merge(base, override)
    assert result["a"]["b"] == 10
    assert result["a"]["c"] == 2
    assert result["d"] == 3


def test_deep_merge_override_replaces_non_dict():
    """_deep_merge should replace non-dict values."""
    base = {"a": [1, 2, 3]}
    override = {"a": [4, 5]}
    result = _deep_merge(base, override)
    assert result["a"] == [4, 5]


# ─── Endpoint tests ───


@pytest.fixture()
def _client() -> TestClient:
    """Create a TestClient with only the system router."""
    app = FastAPI()
    router = system_routes.create_system_router()
    app.include_router(router)
    return TestClient(app)


def test_get_frigate_config_endpoint_missing_file(_client):
    """GET /frigate-config should return empty config when file not found."""
    resp = _client.get("/api/v1/system/frigate-config")
    assert resp.status_code == 200
    data = resp.json()
    assert "config" in data


def test_put_frigate_config_empty_payload(_client):
    """PUT /frigate-config should reject empty payload."""
    resp = _client.put("/api/v1/system/frigate-config", json={})
    assert resp.status_code == 400
