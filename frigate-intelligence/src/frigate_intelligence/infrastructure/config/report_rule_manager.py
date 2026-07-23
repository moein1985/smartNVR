import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from frigate_intelligence.domain.models.report_rule import ReportRule

logger = logging.getLogger(__name__)


class ReportRuleManager:
    def __init__(self, file_path: str = "data/report_rules.json") -> None:
        self._file_path = Path(file_path)
        self._rules: list[ReportRule] = []
        self._load()

    def _load(self) -> None:
        if not self._file_path.exists():
            logger.info(
                "[ReportRules] Rules file not found at %s, starting empty",
                self._file_path,
            )
            self._rules = []
            return
        try:
            raw = self._file_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            self._rules = [ReportRule(**r) for r in data.get("rules", [])]
            logger.info(
                "[ReportRules] Loaded %d rules from %s",
                len(self._rules),
                self._file_path,
            )
        except Exception as e:
            logger.error(
                "[ReportRules] Failed to load rules from %s: %s",
                self._file_path,
                e,
                exc_info=True,
            )
            self._rules = []

    def _save(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"rules": [r.model_dump() for r in self._rules]}
        raw = json.dumps(data, indent=2, ensure_ascii=False)
        self._file_path.write_text(raw, encoding="utf-8")
        logger.info(
            "[ReportRules] Saved %d rules to %s",
            len(self._rules),
            self._file_path,
        )

    def list_rules(self) -> list[ReportRule]:
        return list(self._rules)

    def get_by_id(self, rule_id: str) -> ReportRule | None:
        for r in self._rules:
            if r.id == rule_id:
                return r
        return None

    def create_rule(self, rule: ReportRule) -> ReportRule:
        if not rule.id:
            rule.id = uuid.uuid4().hex
        if not rule.created_at:
            rule.created_at = datetime.now(timezone.utc).isoformat()
        self._rules.append(rule)
        self._save()
        logger.info(
            "[ReportRules] Created rule '%s' (id=%s)",
            rule.name,
            rule.id,
        )
        return rule

    def update_rule(self, rule_id: str, updates: dict) -> ReportRule:
        rule = self.get_by_id(rule_id)
        if not rule:
            raise ValueError(f"Rule '{rule_id}' not found")
        updated = rule.model_copy(update=updates)
        idx = self._rules.index(rule)
        self._rules[idx] = updated
        self._save()
        logger.info(
            "[ReportRules] Updated rule '%s' (id=%s)",
            updated.name,
            updated.id,
        )
        return updated

    def delete_rule(self, rule_id: str) -> bool:
        rule = self.get_by_id(rule_id)
        if not rule:
            raise ValueError(f"Rule '{rule_id}' not found")
        self._rules.remove(rule)
        self._save()
        logger.info(
            "[ReportRules] Deleted rule '%s' (id=%s)",
            rule.name,
            rule.id,
        )
        return True

    def update_status(
        self,
        rule_id: str,
        last_run: str,
        last_status: str,
    ) -> None:
        rule = self.get_by_id(rule_id)
        if not rule:
            return
        rule.last_run = last_run
        rule.last_status = last_status
        self._save()
