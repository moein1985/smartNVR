"""Frigate config service — reads and safely updates keys in frigate.yml."""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_FRIGATE_CONFIG_PATH = Path("/config/frigate.yml")


class FrigateConfigService:
    """Reads and partially updates the host's frigate.yml configuration."""

    def __init__(self, config_path: Path | str | None = None):
        if config_path is None:
            config_path = _DEFAULT_FRIGATE_CONFIG_PATH
        self._config_path = Path(config_path)

    def read(self) -> dict[str, Any]:
        if not self._config_path.exists():
            logger.warning(f"Frigate config not found at {self._config_path}")
            return {}
        try:
            with self._config_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, yaml.YAMLError) as e:
            logger.error(f"Failed to read frigate config: {e}")
            raise

    def update(self, partial: dict[str, Any]) -> dict[str, Any]:
        """Deep-merge partial updates into the existing config and write back."""
        current = self.read()
        merged = _deep_merge(current, partial)
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with self._config_path.open("w", encoding="utf-8") as f:
                yaml.dump(merged, f, default_flow_style=False, sort_keys=True)
            logger.info(f"Frigate config updated at {self._config_path}")
        except OSError as e:
            logger.error(f"Failed to write frigate config: {e}")
            raise
        return merged


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base. Override values win."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
