import asyncio
import datetime
import logging

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from frigate_intelligence.config.dependencies import Container
from frigate_intelligence.domain.entities.notification import Notification
from frigate_intelligence.domain.models.settings_model import SettingsModel
from frigate_intelligence.infrastructure.config.settings_manager import (
    SettingsManager,
)
from frigate_intelligence.infrastructure.notifiers.telegram_notifier import (
    TelegramNotifier,
)
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLRequest,
)

logger = logging.getLogger(__name__)

_REPORT_PROMPT = (
    "Summarize today's events for all _table and _sensitive zones. "
    "Group them by person/zone and provide total active hours and security alerts. "
    "Include first_seen, last_seen, and total_minutes for each person at a _table zone. "
    "List all detections in _sensitive zones with timestamps."
)

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0


def _parse_report_time(report_time: str) -> tuple[int, int]:
    parts = report_time.split(":")
    if len(parts) != 2:
        return 21, 0
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return 21, 0


def _format_report(response, report_date: str) -> str:
    rows = response.result.rows
    columns = response.result.columns

    if not rows:
        return f"📊 Daily Security & HR Report — {report_date}\n\nNo activity detected in monitored zones today."

    table_rows = []
    sensitive_rows = []

    zones_idx = None
    sub_label_idx = None
    for i, col in enumerate(columns):
        if col == "zones":
            zones_idx = i
        elif col == "sub_label":
            sub_label_idx = i

    for row in rows:
        row_zones = str(row[zones_idx]) if zones_idx is not None else ""
        if "_table" in row_zones:
            table_rows.append(row)
        elif "_sensitive" in row_zones:
            sensitive_rows.append(row)
        else:
            table_rows.append(row)

    lines = [f"📊 Daily Security & HR Report — {report_date}", ""]

    if table_rows:
        lines.append("🏢 Workstation Activity:")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        for row in table_rows:
            row_dict = dict(zip(columns, row))
            sub_label = row_dict.get("sub_label", "unknown")
            zones = row_dict.get("zones", "")
            first_seen = row_dict.get("first_seen", "")
            last_seen = row_dict.get("last_seen", "")
            total_minutes = row_dict.get("total_minutes", "")
            event_count = row_dict.get("event_count", "")
            if total_minutes:
                hours = float(total_minutes) / 60.0
                lines.append(f"👤 {sub_label} ({zones}):")
                lines.append(f"   First seen: {first_seen} | Last seen: {last_seen} | Active: ~{hours:.1f}h")
            elif event_count:
                lines.append(f"👤 {sub_label} ({zones}): {event_count} events, {first_seen} → {last_seen}")
            else:
                lines.append(f"👤 {sub_label} ({zones}): {first_seen} → {last_seen}")
        lines.append("")

    if sensitive_rows:
        lines.append("🔒 Restricted Area Alerts:")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        for row in sensitive_rows:
            row_dict = dict(zip(columns, row))
            zones = row_dict.get("zones", "")
            sub_label = row_dict.get("sub_label", "unknown")
            start_time = row_dict.get("start_time", "")
            camera = row_dict.get("camera", "")
            lines.append(f"⚠️ {zones}: {start_time} — {sub_label} detected ({camera})")
        lines.append("")

    total_employees = len({str(r[sub_label_idx]) for r in table_rows}) if sub_label_idx is not None and table_rows else 0
    total_alerts = len(sensitive_rows)
    lines.append(f"📈 Summary: {total_employees} employees tracked, {total_alerts} security alerts.")

    return "\n".join(lines)


async def generate_and_send_report(
    settings_manager: SettingsManager,
    container: Container,
) -> None:
    settings: SettingsModel = settings_manager.load()

    if not settings.telegram_enabled or not settings.telegram_bot_token:
        logger.info("Telegram reporting is disabled, skipping report generation")
        return

    tz = pytz.timezone(settings.report_timezone)
    now_in_tz = datetime.datetime.now(tz)
    report_date = now_in_tz.strftime("%Y-%m-%d")
    logger.info(f"Generating daily report for {report_date} ({settings.report_timezone})")

    try:
        offset_minutes = int(tz.utcoffset(now_in_tz).total_seconds() / 60)
        client_tz_info = {
            "timezone": settings.report_timezone,
            "offset_minutes": offset_minutes,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp(),
        }

        req = TextToSQLRequest(
            question=_REPORT_PROMPT,
            max_retries=3,
            client_tz_info=client_tz_info,
        )
        response = container.text_to_sql_use_case.execute(req)
        message = _format_report(response, report_date)
    except Exception as e:
        logger.error(f"Failed to generate report via LLM: {e}")
        message = f"📊 Daily Security & HR Report — {report_date}\n\n⚠️ Report generation failed: {e}"

    notifier = TelegramNotifier(
        bot_token=settings.telegram_bot_token,
        default_chat_id=settings.telegram_chat_id,
    )
    notification = Notification(message=message)

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            success = await notifier.send(notification)
            if success:
                logger.info(f"Report sent to Telegram successfully (attempt {attempt})")
                return
            logger.warning(f"Telegram send returned False (attempt {attempt}/{_MAX_RETRIES})")
        except Exception as e:
            logger.warning(f"Telegram send failed (attempt {attempt}/{_MAX_RETRIES}): {e}")

        if attempt < _MAX_RETRIES:
            delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.info(f"Retrying in {delay}s...")
            await asyncio.sleep(delay)

    logger.error(f"Failed to send Telegram report after {_MAX_RETRIES} attempts")


class CronService:
    def __init__(
        self,
        settings_manager: SettingsManager,
        container: Container | None = None,
    ) -> None:
        self._settings_manager = settings_manager
        self._container = container
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self._refresh_job()
        self._scheduler.start()
        logger.info("Cron scheduler started")

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Cron scheduler stopped")

    def _refresh_job(self) -> None:
        settings = self._settings_manager.load()

        existing = self._scheduler.get_job("report_job")
        if existing:
            self._scheduler.remove_job("report_job")

        if not settings.telegram_enabled:
            logger.info("Telegram reporting is disabled, no job scheduled")
            return

        hour, minute = _parse_report_time(settings.report_time)

        try:
            tz = pytz.timezone(settings.report_timezone)
        except Exception:
            logger.warning(
                f"Invalid timezone '{settings.report_timezone}', falling back to UTC"
            )
            tz = pytz.UTC

        trigger = CronTrigger(hour=hour, minute=minute, timezone=tz)
        self._scheduler.add_job(
            generate_and_send_report,
            trigger=trigger,
            args=[self._settings_manager, self._container],
            id="report_job",
            replace_existing=True,
        )
        logger.info(
            f"Scheduled report job at {hour:02d}:{minute:02d} {settings.report_timezone}"
        )
