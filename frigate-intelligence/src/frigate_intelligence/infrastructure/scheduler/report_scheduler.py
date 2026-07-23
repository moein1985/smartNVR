import asyncio
import datetime
import logging

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from frigate_intelligence.config.dependencies import Container
from frigate_intelligence.domain.entities.notification import Notification
from frigate_intelligence.domain.models.report_rule import ReportRule
from frigate_intelligence.domain.models.settings_model import SettingsModel
from frigate_intelligence.infrastructure.config.report_rule_manager import (
    ReportRuleManager,
)
from frigate_intelligence.infrastructure.config.report_history_manager import (
    ReportHistoryManager,
)
from frigate_intelligence.infrastructure.config.settings_manager import (
    SettingsManager,
)
from frigate_intelligence.infrastructure.notifiers.notifier_factory import (
    NotifierFactory,
)
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLRequest,
)

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0


def _build_dynamic_prompt(
    rule: ReportRule,
    settings: SettingsModel,
) -> str:
    if rule.prompt_template:
        prompt = rule.prompt_template
    else:
        parts = [
            f"Summarize events for the past {rule.interval_hours} hours.",
        ]

        if rule.zones:
            zone_hints = []
            for z in rule.zones:
                if z.endswith("_table"):
                    person_hint = z.rsplit("_table", 1)[0]
                    zone_hints.append(
                        f"zone '{z}' tracks person '{person_hint}' at a workstation"
                    )
                elif z.endswith("_sensitive"):
                    zone_hints.append(
                        f"zone '{z}' is a sensitive/security area"
                    )
                else:
                    zone_hints.append(f"zone '{z}'")
            parts.append("Zones: " + "; ".join(zone_hints) + ".")

        if rule.cameras:
            parts.append(f"Cameras: {', '.join(rule.cameras)}.")
        if rule.labels:
            parts.append(f"Labels: {', '.join(rule.labels)}.")

        parts.append(
            "Group results by person/zone and provide total active hours "
            "and security alerts. Include first_seen, last_seen, "
            "and total_minutes for each person at a _table zone. "
            "List all detections in _sensitive zones with timestamps."
        )
        prompt = " ".join(parts)

    work_hours = (
        f" Working hours are {settings.work_hours_start} to "
        f"{settings.work_hours_end} ({rule.timezone}). "
        "Consider whether events occurred within or outside working hours."
    )
    prompt += work_hours

    return prompt


def _format_report(response, report_date: str, interval_hours: int) -> str:
    rows = response.result.rows
    columns = response.result.columns

    if not rows:
        return (
            f"📊 گزارش — {report_date}\n\n"
            f"در {interval_hours} ساعت گذشته، هیچ فعالیت‌ای ثبت نشده است."
        )

    lines = [f"📊 گزارش — {report_date}", ""]

    for row in rows:
        row_dict = dict(zip(columns, row))
        sub_label = row_dict.get("sub_label", "unknown")
        zones = row_dict.get("zones", "")
        first_seen = row_dict.get("first_seen", "")
        last_seen = row_dict.get("last_seen", "")
        total_minutes = row_dict.get("total_minutes", "")
        event_count = row_dict.get("event_count", "")

        if total_minutes:
            hours = float(total_minutes) / 60.0
            lines.append(
                f"👤 {sub_label} ({zones}): "
                f"{first_seen} → {last_seen} | فعال: ~{hours:.1f} ساعت"
            )
        elif event_count:
            lines.append(
                f"👤 {sub_label} ({zones}): {event_count} رویداد, "
                f"{first_seen} → {last_seen}"
            )
        else:
            lines.append(f"👤 {sub_label} ({zones}): {first_seen} → {last_seen}")

    lines.append("")
    lines.append(f"📈 مجموع: {len(rows)} رکورد.")

    return "\n".join(lines)


class ReportScheduler:
    def __init__(
        self,
        settings_manager: SettingsManager,
        rule_manager: ReportRuleManager,
        history_manager: ReportHistoryManager,
        container: Container | None = None,
    ) -> None:
        self._settings_manager = settings_manager
        self._rule_manager = rule_manager
        self._history_manager = history_manager
        self._container = container
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        rules = self._rule_manager.list_rules()
        for rule in rules:
            if rule.enabled:
                self._schedule_rule(rule)
        self._scheduler.start()
        logger.info(
            "[ReportScheduler] Started with %d enabled rules",
            sum(1 for r in rules if r.enabled),
        )

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("[ReportScheduler] Stopped")

    def _schedule_rule(self, rule: ReportRule) -> None:
        job_id = f"report_rule_{rule.id}"
        interval = rule.interval_hours if rule.interval_hours >= 1 else 24

        trigger = IntervalTrigger(hours=interval)
        self._scheduler.add_job(
            self._execute_rule,
            trigger=trigger,
            args=[rule.id],
            id=job_id,
            replace_existing=True,
        )
        logger.info(
            "[ReportScheduler] Scheduled rule '%s' (id=%s) every %dh",
            rule.name,
            rule.id,
            interval,
        )

    def refresh_rule(self, rule_id: str) -> None:
        rule = self._rule_manager.get_by_id(rule_id)
        job_id = f"report_rule_{rule_id}"

        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            logger.info(
                "[ReportScheduler] Removed existing job for rule %s",
                rule_id,
            )

        if rule and rule.enabled:
            self._schedule_rule(rule)
        else:
            logger.info(
                "[ReportScheduler] Rule %s is disabled or not found, no job scheduled",
                rule_id,
            )

    def remove_rule(self, rule_id: str) -> None:
        job_id = f"report_rule_{rule_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            logger.info(
                "[ReportScheduler] Removed job for deleted rule %s",
                rule_id,
            )

    async def _execute_rule(self, rule_id: str) -> None:
        rule = self._rule_manager.get_by_id(rule_id)
        if not rule:
            logger.warning(
                "[ReportScheduler] Rule %s not found, skipping execution",
                rule_id,
            )
            return
        if not rule.enabled:
            logger.info(
                "[ReportScheduler] Rule '%s' is disabled, skipping",
                rule.name,
            )
            return

        settings = self._settings_manager.load()
        tz = pytz.timezone(rule.timezone)
        now_in_tz = datetime.datetime.now(tz)
        report_date = now_in_tz.strftime("%Y-%m-%d")

        logger.info(
            "[ReportScheduler] Executing rule '%s' (id=%s) for %s, interval=%dh",
            rule.name,
            rule.id,
            report_date,
            rule.interval_hours,
        )

        message = ""
        status = "success"

        try:
            if not self._container:
                raise RuntimeError("DI container is not available")

            offset_minutes = int(now_in_tz.utcoffset().total_seconds() / 60)
            client_tz_info = {
                "timezone": rule.timezone,
                "offset_minutes": offset_minutes,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp(),
            }

            prompt = _build_dynamic_prompt(rule, settings)
            req = TextToSQLRequest(
                question=prompt,
                max_retries=3,
                client_tz_info=client_tz_info,
            )
            response = self._container.text_to_sql_use_case.execute(req)
            message = _format_report(response, report_date, rule.interval_hours)

            if rule.include_summary and response.explanation:
                message = (
                    f"در {rule.interval_hours} ساعت گذشته:\n\n"
                    f"{response.explanation}\n\n{message}"
                )

        except Exception as e:
            logger.error(
                "[ReportScheduler] Failed to execute rule '%s': %s",
                rule.name,
                e,
                exc_info=True,
            )
            status = "error"
            message = f"📊 گزارش — {report_date}\n\n⚠️ خطا در تولید گزارش: {e}"

        notifier_factory = NotifierFactory(
            telegram_bot_token=settings.telegram_bot_token,
            telegram_chat_id=settings.telegram_chat_id,
            bale_bot_token=settings.bale_bot_token,
            bale_chat_id=settings.bale_chat_id,
        )

        notification = Notification(message=message)
        chat_id = rule.chat_id or None

        sent = False
        for attempt in range(1, _MAX_RETRIES + 1):
            sent = await notifier_factory.send(
                rule.destination,
                notification,
                chat_id=chat_id,
            )
            if sent:
                logger.info(
                    "[ReportScheduler] Rule '%s' report sent to %s (attempt %d)",
                    rule.name,
                    rule.destination,
                    attempt,
                )
                break
            logger.warning(
                "[ReportScheduler] Send attempt %d/%d failed for rule '%s'",
                attempt,
                _MAX_RETRIES,
                rule.name,
            )
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        if not sent:
            status = "send_failed"
            logger.error(
                "[ReportScheduler] Failed to send report for rule '%s' after %d attempts",
                rule.name,
                _MAX_RETRIES,
            )

        self._rule_manager.update_status(
            rule_id,
            last_run=now_in_tz.isoformat(),
            last_status=status,
        )

        self._history_manager.add_entry(
            rule_id=rule.id,
            rule_name=rule.name,
            status=status,
            message_preview=message[:200],
            destination=rule.destination,
        )

    async def execute_rule_now(self, rule_id: str) -> dict:
        rule = self._rule_manager.get_by_id(rule_id)
        if not rule:
            raise ValueError(f"Rule '{rule_id}' not found")

        logger.info(
            "[ReportScheduler] Manual test trigger for rule '%s' (id=%s)",
            rule.name,
            rule.id,
        )
        await self._execute_rule(rule_id)
        rule = self._rule_manager.get_by_id(rule_id)
        return {
            "status": rule.last_status if rule else "unknown",
            "message": "Test execution completed",
        }
