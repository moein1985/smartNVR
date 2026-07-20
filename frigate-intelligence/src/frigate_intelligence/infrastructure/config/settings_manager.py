import json
import logging
from pathlib import Path

from frigate_intelligence.domain.models.settings_model import SettingsModel

logger = logging.getLogger(__name__)

_DEFAULT_SETTINGS = SettingsModel()


class SettingsManager:
    def __init__(self, file_path: str = "settings.json") -> None:
        self._file_path = Path(file_path)

    def load(self) -> SettingsModel:
        if not self._file_path.exists():
            logger.info(
                f"Settings file not found at {self._file_path}, returning defaults"
            )
            return _DEFAULT_SETTINGS.model_copy()
        try:
            raw = self._file_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return SettingsModel(**data)
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}, returning defaults")
            return _DEFAULT_SETTINGS.model_copy()

    def save(self, settings: SettingsModel) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        raw = settings.model_dump_json(indent=2)
        self._file_path.write_text(raw, encoding="utf-8")
        logger.info(f"Settings saved to {self._file_path}")
