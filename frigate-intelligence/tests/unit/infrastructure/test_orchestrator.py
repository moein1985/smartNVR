"""Unit tests for hardware_discovery, container_manager, and compose_override."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from frigate_intelligence.infrastructure.orchestrator.hardware_discovery import (
    GpuInfo,
    HardwareDiscovery,
    HardwareInfo,
)
from frigate_intelligence.infrastructure.orchestrator.container_manager import (
    ContainerManager,
)
from frigate_intelligence.infrastructure.orchestrator.compose_override import (
    ComposeOverrideGenerator,
    ResourceAssignment,
)


# ─── Hardware Discovery Tests ───


def _make_mem(total=16 * 1024**3, available=8 * 1024**3, percent=50.0):
    mem = MagicMock()
    mem.total = total
    mem.available = available
    mem.percent = percent
    return mem


def test_hardware_discovery_cpu_and_memory():
    """HardwareDiscovery should report CPU cores and memory info via psutil."""
    hd = HardwareDiscovery()
    with patch("frigate_intelligence.infrastructure.orchestrator.hardware_discovery.psutil") as mock_psutil:
        mock_psutil.cpu_percent.return_value = 42.5
        mock_psutil.virtual_memory.return_value = _make_mem()
        with patch.object(hd, "_discover_gpus", return_value=[]):
            info = hd.discover()

    assert info.cpu_cores > 0
    assert info.cpu_percent == 42.5
    assert info.memory_total_gb == pytest.approx(16.0, abs=0.01)
    assert info.memory_available_gb == pytest.approx(8.0, abs=0.01)
    assert info.memory_used_pct == 50.0
    assert info.gpus == []


def test_hardware_discovery_gpu_parsing():
    """_parse_gpu_output should correctly parse nvidia-smi CSV output."""
    hd = HardwareDiscovery()
    output = "0, NVIDIA GeForce RTX 4090, 24564, 1024, 15.5, GPU-abc-123\n1, NVIDIA GeForce RTX 4090, 24564, 512, 0.0, GPU-def-456\n"
    gpus = hd._parse_gpu_output(output)

    assert len(gpus) == 2
    assert gpus[0].index == 0
    assert gpus[0].name == "NVIDIA GeForce RTX 4090"
    assert gpus[0].memory_total_mb == 24564
    assert gpus[0].memory_used_mb == 1024
    assert gpus[0].gpu_utilization_pct == 15.5
    assert gpus[0].uuid == "GPU-abc-123"
    assert gpus[1].index == 1
    assert gpus[1].uuid == "GPU-def-456"


def test_hardware_discovery_gpu_empty_output():
    """_parse_gpu_output should return empty list for empty output."""
    hd = HardwareDiscovery()
    assert hd._parse_gpu_output("") == []
    assert hd._parse_gpu_output("   \n  \n") == []


def test_hardware_discovery_gpu_malformed_line():
    """_parse_gpu_output should skip lines with insufficient fields."""
    hd = HardwareDiscovery()
    output = "0, RTX 4090, 24564\n1, RTX 4090, 24564, 1024, 15.5, GPU-def-456\n"
    gpus = hd._parse_gpu_output(output)

    assert len(gpus) == 1
    assert gpus[0].index == 1


def test_hardware_discovery_nvidia_smi_not_found():
    """_discover_gpus should return empty list if nvidia-smi is not installed."""
    hd = HardwareDiscovery()
    with patch("subprocess.run", side_effect=FileNotFoundError):
        gpus = hd._discover_gpus()
    assert gpus == []


def test_hardware_discovery_nvidia_smi_timeout():
    """_discover_gpus should return empty list on timeout."""
    hd = HardwareDiscovery()
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=10)):
        gpus = hd._discover_gpus()
    assert gpus == []


def test_hardware_discovery_nvidia_smi_nonzero_return():
    """_discover_gpus should return empty list when nvidia-smi returns non-zero."""
    hd = HardwareDiscovery()
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "No NVIDIA devices found"
    with patch("subprocess.run", return_value=mock_result):
        gpus = hd._discover_gpus()
    assert gpus == []


def test_hardware_info_to_dict():
    """HardwareInfo.to_dict should produce a serializable dict."""
    info = HardwareInfo(
        cpu_cores=8,
        cpu_percent=25.0,
        memory_total_gb=16.0,
        memory_available_gb=8.0,
        memory_used_pct=50.0,
        gpus=[GpuInfo(index=0, name="RTX 4090", memory_total_mb=24564, memory_used_mb=1024, gpu_utilization_pct=15.5, uuid="GPU-abc")],
    )
    d = info.to_dict()
    assert d["cpu"]["cores"] == 8
    assert d["cpu"]["utilization_pct"] == 25.0
    assert d["memory"]["total_gb"] == 16.0
    assert d["gpus"][0]["name"] == "RTX 4090"
    assert d["gpus"][0]["uuid"] == "GPU-abc"


# ─── Container Manager Tests ───


def _make_mock_container(name="frigate-intelligence", image_tag="frigate-intelligence:latest", status="running", short_id="abc123", ports=None):
    c = MagicMock()
    c.name = name
    c.image.tags = [image_tag]
    c.image.id = "sha256:abc"
    c.status = status
    c.short_id = short_id
    c.ports = ports or {}
    return c


def _make_mock_client(containers=None):
    client = MagicMock()
    client.containers.list.return_value = containers or []
    return client


def test_container_manager_list_running():
    """ContainerManager should list running containers with info."""
    mock_c = _make_mock_container()
    client = _make_mock_client(containers=[mock_c])
    manager = ContainerManager(client=client)
    result = manager.list_containers()

    assert len(result) == 1
    assert result[0].name == "frigate-intelligence"
    assert result[0].image == "frigate-intelligence:latest"
    assert result[0].status == "running"


def test_container_manager_list_empty():
    """ContainerManager should return empty list when no containers running."""
    client = _make_mock_client(containers=[])
    manager = ContainerManager(client=client)
    assert manager.list_containers() == []


def test_container_manager_to_dict_list():
    """to_dict_list should serialize containers to dicts."""
    mock_c = _make_mock_container(ports={"8080/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]})
    client = _make_mock_client(containers=[mock_c])
    manager = ContainerManager(client=client)
    result = manager.to_dict_list()

    assert len(result) == 1
    assert result[0]["name"] == "frigate-intelligence"
    assert result[0]["ports"][0]["host_port"] == "8080"


def test_container_manager_docker_not_installed():
    """ContainerManager should return empty list if docker package is missing."""
    manager = ContainerManager()
    with patch.object(manager, "_get_client", side_effect=ImportError("No module named 'docker'")):
        assert manager.list_containers() == []


def test_container_manager_handles_exception():
    """ContainerManager should return empty list on Docker API errors."""
    client = MagicMock()
    client.containers.list.side_effect = Exception("Docker daemon not running")
    manager = ContainerManager(client=client)
    assert manager.list_containers() == []


def test_container_manager_all_statuses():
    """ContainerManager should pass all_statuses to docker client."""
    client = _make_mock_client()
    manager = ContainerManager(client=client)
    manager.list_containers(all_statuses=True)
    client.containers.list.assert_called_once_with(all=True)


# ─── Compose Override Tests ───


def test_compose_override_generate_basic():
    """generate should produce correct YAML structure for cpuset assignment."""
    gen = ComposeOverrideGenerator()
    assignments = [
        ResourceAssignment(service="frigate-intelligence", cpuset="0-7"),
    ]
    result = gen.generate(assignments)

    assert "services" in result
    assert "frigate-intelligence" in result["services"]
    assert result["services"]["frigate-intelligence"]["cpuset"] == "0-7"


def test_compose_override_generate_with_gpu():
    """generate should include GPU device reservations."""
    gen = ComposeOverrideGenerator()
    assignments = [
        ResourceAssignment(service="frigate-intelligence", gpu_ids=[0, 1]),
    ]
    result = gen.generate(assignments)

    svc = result["services"]["frigate-intelligence"]
    assert "deploy" in svc
    devices = svc["deploy"]["resources"]["reservations"]["devices"]
    assert len(devices) == 1
    assert devices[0]["driver"] == "nvidia"
    assert devices[0]["device_ids"] == ["0", "1"]


def test_compose_override_generate_with_memory():
    """generate should include memory limit."""
    gen = ComposeOverrideGenerator()
    assignments = [
        ResourceAssignment(service="frigate", memory_limit="4g"),
    ]
    result = gen.generate(assignments)
    assert result["services"]["frigate"]["mem_limit"] == "4g"


def test_compose_override_generate_multiple_services():
    """generate should handle multiple service assignments."""
    gen = ComposeOverrideGenerator()
    assignments = [
        ResourceAssignment(service="frigate", cpuset="0-3"),
        ResourceAssignment(service="frigate-intelligence", cpuset="4-7", gpu_ids=[0]),
    ]
    result = gen.generate(assignments)
    assert len(result["services"]) == 2
    assert result["services"]["frigate"]["cpuset"] == "0-3"
    assert result["services"]["frigate-intelligence"]["cpuset"] == "4-7"


def test_compose_override_generate_empty():
    """generate with no assignments should produce empty services."""
    gen = ComposeOverrideGenerator()
    result = gen.generate([])
    assert result["services"] == {}


def test_compose_override_write_file(tmp_path):
    """write should create a YAML file on disk."""
    out = tmp_path / "docker-compose.override.yml"
    gen = ComposeOverrideGenerator(output_path=out)
    assignments = [
        ResourceAssignment(service="frigate-intelligence", cpuset="0-7", gpu_ids=[0]),
    ]
    path = gen.write(assignments)

    assert path == out
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "frigate-intelligence" in content
    assert "cpuset" in content
    assert "nvidia" in content


def test_compose_override_read_existing(tmp_path):
    """read_existing should parse an existing override file."""
    out = tmp_path / "override.yml"
    out.write_text("version: '3.8'\nservices:\n  frigate:\n    cpuset: '0-3'\n", encoding="utf-8")
    gen = ComposeOverrideGenerator(output_path=out)
    data = gen.read_existing()
    assert data["services"]["frigate"]["cpuset"] == "0-3"


def test_compose_override_read_existing_no_file(tmp_path):
    """read_existing should return empty dict when file doesn't exist."""
    gen = ComposeOverrideGenerator(output_path=tmp_path / "nonexistent.yml")
    assert gen.read_existing() == {}
