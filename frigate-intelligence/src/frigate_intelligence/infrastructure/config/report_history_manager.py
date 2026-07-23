import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from frigate_intelligence.domain.models.report_history import ReportHistoryEntry

logger = logging.getLogger(__name__)

_MAX_ENTRIES = 100


class ReportHistoryManager:
    def __init__(self, file_path: str = "data/report_history.json") -> None:
        self._file_path = Path(file_path)
        self._entries: list[ReportHistoryEntry] = []
        self._load()

    def _load(self) -> None:
        if not self._file_path.exists():
            logger.info(
                "[ReportRules] History file not found at %s, starting empty",
                self._file_path,
            )
            self._entries = []
            return
        try:
            raw = self._file_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            self._entries = [ReportHistoryEntry(**e) for e in data.get("entries", [])]
            logger.info(
                "[ReportRules] Loaded %d history entries from %s",
                len(self._entries),
                self._file_path,
            )
        except Exception as e:
            logger.error(
                "[ReportRules] Failed to load history from %s: %s",
                self._file_path,
                e,
                exc_info=True,
            )
            self._entries = []

    def _save(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"entries": [e.model_dump() for e in self._entries]}
        raw = json.dumps(data, indent=2, ensure_ascii=False)
        self._file_path.write_text(raw, encoding="utf-8")

    def add_entry(
        self,
        rule_id: str,
        rule_name: str,
        status: str,
        message_preview: str = "",
        destination: str = "",
    ) -> ReportHistoryEntry:
        entry = ReportHistoryEntry(
            id=uuid.uuid4().hex,
            rule_id=rule_id,
            rule_name=rule_name,
            executed_at=datetime.now(timezone.utc).isoformat(),
            status=status,
            message_preview=message_preview[:200],
            destination=destination,
        )
        self._entries.append(entry)

        while len(self._entries) > _MAX_ENTRIES:
            evicted = self._entries.pop(0)
            logger.info(
                "[ReportRules] FIFO evicted history entry %s (rule=%s)",
                evicted.id,
                evicted.rule_name,
            )

        self._save()
        logger.info(
            "[ReportRules] Added history entry for rule '%s' (status=%s, total=%d)",
            rule_name,
            status,
            len(self._entries),
        )
        return entry

    def list_entries(self, limit: int = 50) -> list[ReportHistoryEntry]:
        return list(reversed(self._entries))[:limit]

    def list_by_rule(self, rule_id: str, limit: int = 20) -> list[ReportHistoryEntry]:
        result = [e for e in reversed(self._entries) if e.rule_id == rule_id]
        return result[:limit]

    def count(self) -> int:
        return len(self._entries)
