"""Compose override generator — writes docker-compose.override.yml for resource pinning."""

import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ResourceAssignment:
    """Desired resource assignment for a single service."""
    service: str
    cpuset: str | None = None
    gpu_ids: list[int] | None = None
    memory_limit: str | None = None


class ComposeOverrideGenerator:
    """Generates/updates a docker-compose.override.yml file safely."""

    def __init__(self, output_path: Path | str | None = None):
        if output_path is None:
            output_path = Path("docker-compose.override.yml")
        self._output_path = Path(output_path)

    def generate(self, assignments: list[ResourceAssignment]) -> dict[str, Any]:
        services: dict[str, Any] = {}
        for assignment in assignments:
            service_def: dict[str, Any] = {}
            if assignment.cpuset:
                service_def["cpuset"] = assignment.cpuset
            if assignment.memory_limit:
                service_def["mem_limit"] = assignment.memory_limit
            if assignment.gpu_ids:
                service_def["deploy"] = {
                    "resources": {
                        "reservations": {
                            "devices": [
                                {
                                    "driver": "nvidia",
                                    "device_ids": [str(gid) for gid in assignment.gpu_ids],
                                    "capabilities": ["gpu"],
                                }
                            ]
                        }
                    }
                }
            if service_def:
                services[assignment.service] = service_def

        override = {"version": "3.8", "services": services}
        return override

    def write(self, assignments: list[ResourceAssignment]) -> Path:
        override = self.generate(assignments)
        try:
            self._output_path.parent.mkdir(parents=True, exist_ok=True)
            with self._output_path.open("w", encoding="utf-8") as f:
                yaml.dump(override, f, default_flow_style=False, sort_keys=True)
            logger.info(f"Compose override written to {self._output_path}")
        except OSError as e:
            logger.error(f"Failed to write override file: {e}")
            raise

        return self._output_path

    def read_existing(self) -> dict[str, Any]:
        if not self._output_path.exists():
            return {}
        try:
            with self._output_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, yaml.YAMLError) as e:
            logger.warning(f"Failed to read existing override: {e}")
            return {}
