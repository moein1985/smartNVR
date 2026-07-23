"""Regression tests for Phase 16.4 — Container Capability Checker.

Tests: test_feat_016_4_capability_gpu_container, test_feat_016_4_capability_cpu_container,
       test_feat_016_4_capability_pattern_match_tensorrt, test_feat_016_4_capability_pattern_match_cuda
"""

from unittest.mock import MagicMock

from frigate_intelligence.infrastructure.orchestrator.container_capability import (
    ContainerCapabilityChecker,
)


def _make_container(
    name: str = "test-container",
    image_tags: list[str] | None = None,
    device_requests: list[dict] | None = None,
):
    container = MagicMock()
    container.name = name
    container.attrs = {
        "HostConfig": {
            "DeviceRequests": device_requests or [],
        }
    }
    image = MagicMock()
    image.tags = image_tags or []
    image.id = "sha256:abc123"
    container.image = image
    return container


def test_feat_016_4_capability_gpu_container():
    """Container with NVIDIA DeviceRequests is detected as GPU-capable."""
    container = _make_container(
        name="trt-server",
        device_requests=[
            {"Driver": "nvidia", "DeviceIDs": ["0", "1"]},
        ],
    )
    checker = ContainerCapabilityChecker()
    result = checker.check(container)

    assert result.supports_gpu is True
    assert result.detection_strategy == "device_requests"
    assert "NVIDIA" in result.details


def test_feat_016_4_capability_cpu_container():
    """Container without GPU indicators defaults to CPU-only."""
    container = _make_container(
        name="web-server",
        image_tags=["nginx:latest"],
        device_requests=[],
    )
    checker = ContainerCapabilityChecker()
    result = checker.check(container)

    assert result.supports_gpu is False
    assert result.detection_strategy == "cpu_only"


def test_feat_016_4_capability_pattern_match_tensorrt():
    """Image name containing 'tensorrt' is detected as GPU-capable."""
    container = _make_container(
        name="trt-detector",
        image_tags=["nvcr.io/nvidia/tensorrt:24.01"],
        device_requests=[],
    )
    checker = ContainerCapabilityChecker()
    result = checker.check(container)

    assert result.supports_gpu is True
    assert result.detection_strategy == "image_pattern"
    assert "tensorrt" in result.details


def test_feat_016_4_capability_pattern_match_cuda():
    """Image name containing 'cuda' is detected as GPU-capable."""
    container = _make_container(
        name="cuda-app",
        image_tags=["nvidia/cuda:12.2-runtime"],
        device_requests=[],
    )
    checker = ContainerCapabilityChecker()
    result = checker.check(container)

    assert result.supports_gpu is True
    assert result.detection_strategy == "image_pattern"
    assert "cuda" in result.details


def test_feat_016_4_capability_device_requests_takes_priority():
    """DeviceRequests strategy takes priority over image pattern."""
    container = _make_container(
        name="gpu-container",
        image_tags=["nvidia/cuda:12.2"],
        device_requests=[{"Driver": "nvidia", "DeviceIDs": ["0"]}],
    )
    checker = ContainerCapabilityChecker()
    result = checker.check(container)

    assert result.supports_gpu is True
    assert result.detection_strategy == "device_requests"


def test_feat_016_4_capability_nvidia_slash_pattern():
    """Image name containing 'nvidia/' is detected as GPU-capable."""
    container = _make_container(
        name="nvidia-app",
        image_tags=["nvidia/deepstream:6.3"],
        device_requests=[],
    )
    checker = ContainerCapabilityChecker()
    result = checker.check(container)

    assert result.supports_gpu is True
    assert result.detection_strategy == "image_pattern"
    assert "nvidia/" in result.details


def test_feat_016_4_capability_error_handling():
    """Checker handles errors gracefully and returns CPU-only."""
    container = MagicMock()
    container.name = "broken-container"
    container.attrs = None

    checker = ContainerCapabilityChecker()
    result = checker.check(container)

    assert result.supports_gpu is False
    assert result.detection_strategy in ("cpu_only", "error")
