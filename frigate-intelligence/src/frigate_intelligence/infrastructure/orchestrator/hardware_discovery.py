"""Hardware discovery module — detects CPU, RAM, and GPU resources."""

import logging
import os
import subprocess
from dataclasses import dataclass, field

import psutil

logger = logging.getLogger(__name__)


@dataclass
class GpuInfo:
    index: int
    name: str
    memory_total_mb: int
    memory_used_mb: int
    gpu_utilization_pct: float
    uuid: str


@dataclass
class HardwareInfo:
    cpu_cores: int = 0
    cpu_percent: float = 0.0
    memory_total_gb: float = 0.0
    memory_available_gb: float = 0.0
    memory_used_pct: float = 0.0
    gpus: list[GpuInfo] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "cpu": {
                "cores": self.cpu_cores,
                "utilization_pct": round(self.cpu_percent, 1),
            },
            "memory": {
                "total_gb": round(self.memory_total_gb, 2),
                "available_gb": round(self.memory_available_gb, 2),
                "used_pct": round(self.memory_used_pct, 1),
            },
            "gpus": [
                {
                    "index": g.index,
                    "name": g.name,
                    "memory_total_mb": g.memory_total_mb,
                    "memory_used_mb": g.memory_used_mb,
                    "gpu_utilization_pct": g.gpu_utilization_pct,
                    "uuid": g.uuid,
                }
                for g in self.gpus
            ],
        }


_NVIDIA_SMI_ARGS = [
    "nvidia-smi",
    "--query-gpu=index,name,memory.total,memory.used,utilization.gpu,uuid",
    "--format=csv,noheader,nounits",
]


class HardwareDiscovery:
    """Discovers system hardware resources: CPU, RAM, and NVIDIA GPUs."""

    def discover(self) -> HardwareInfo:
        info = HardwareInfo()
        info.cpu_cores = os.cpu_count() or 0
        info.cpu_percent = psutil.cpu_percent(interval=0.5)

        mem = psutil.virtual_memory()
        info.memory_total_gb = mem.total / (1024**3)
        info.memory_available_gb = mem.available / (1024**3)
        info.memory_used_pct = mem.percent

        info.gpus = self._discover_gpus()
        return info

    def _discover_gpus(self) -> list[GpuInfo]:
        try:
            result = subprocess.run(
                _NVIDIA_SMI_ARGS,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except FileNotFoundError:
            logger.info("nvidia-smi not found — no GPUs discovered")
            return []
        except subprocess.TimeoutExpired:
            logger.warning("nvidia-smi timed out")
            return []
        except Exception as e:
            logger.warning(f"Failed to run nvidia-smi: {e}")
            return []

        if result.returncode != 0:
            logger.warning(f"nvidia-smi returned code {result.returncode}: {result.stderr.strip()}")
            return []

        return self._parse_gpu_output(result.stdout)

    def _parse_gpu_output(self, output: str) -> list[GpuInfo]:
        gpus: list[GpuInfo] = []
        for line in output.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 6:
                logger.warning(f"Unexpected nvidia-smi line format: {line}")
                continue
            try:
                gpus.append(
                    GpuInfo(
                        index=int(parts[0]),
                        name=parts[1],
                        memory_total_mb=int(parts[2]),
                        memory_used_mb=int(parts[3]),
                        gpu_utilization_pct=float(parts[4]),
                        uuid=parts[5],
                    )
                )
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse GPU line '{line}': {e}")
        return gpus
