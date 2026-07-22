import asyncio
import datetime
import logging

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

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

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0


def _build_report_prompt(interval_hours: int) -> str:
    return (
        f"Summarize events for the past {interval_hours} hours "
        "for all _table and _sensitive zones. "
        "Group them by person/zone and provide total active hours and security alerts. "
        "Include first_seen, last_seen, and total_minutes for each person at a _table zone. "
        "List all detections in _sensitive zones with timestamps."
    )


def _format_report(response, report_date: str, interval_hours: int) -> str:
    rows = response.result.rows
    columns = response.result.columns

    if not rows:
        return (
            f"📊 گزارش امنیتی و منابع انسانی — {report_date}\n\n"
            f"در {interval_hours} ساعت گذشته، هیچ فعالیت‌ای در مناطق تحت نظارت ثبت نشده است."
        )

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

    lines = [f"📊 گزارش امنیتی و منابع انسانی — {report_date}", ""]

    if table_rows:
        lines.append("🏢 فعالیت در ایستگاه‌های کاری:")
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
                lines.append(f"   اولین مشاهده: {first_seen} | آخرین مشاهده: {last_seen} | فعال: ~{hours:.1f} ساعت")
            elif event_count:
                lines.append(f"👤 {sub_label} ({zones}): {event_count} رویداد, {first_seen} → {last_seen}")
            else:
                lines.append(f"👤 {sub_label} ({zones}): {first_seen} → {last_seen}")
        lines.append("")

    if sensitive_rows:
        lines.append("🔒 هشدارهای مناطق حساس:")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        for row in sensitive_rows:
            row_dict = dict(zip(columns, row))
            zones = row_dict.get("zones", "")
            sub_label = row_dict.get("sub_label", "unknown")
            start_time = row_dict.get("start_time", "")
            camera = row_dict.get("camera", "")
            lines.append(f"⚠️ {zones}: {start_time} — {sub_label} شناسایی شد ({camera})")
        lines.append("")

    total_employees = len({str(r[sub_label_idx]) for r in table_rows}) if sub_label_idx is not None and table_rows else 0
    total_alerts = len(sensitive_rows)
    lines.append(f"📈 خلاصه: {total_employees} کارمند ردیابی شد، {total_alerts} هشدار امنیتی.")

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
    interval_hours = settings.report_interval_hours
    logger.info(
        f"Generating report for {report_date} ({settings.report_timezone}), "
        f"interval={interval_hours}h"
    )

    try:
        offset_minutes = int(now_in_tz.utcoffset().total_seconds() / 60)
        client_tz_info = {
            "timezone": settings.report_timezone,
            "offset_minutes": offset_minutes,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).timestamp(),
        }

        prompt = _build_report_prompt(interval_hours)
        req = TextToSQLRequest(
            question=prompt,
            max_retries=3,
            client_tz_info=client_tz_info,
        )
        response = container.text_to_sql_use_case.execute(req)
        message = _format_report(response, report_date, interval_hours)

        if response.result.row_count > 0:
            explanation = response.explanation
            if explanation:
                message = (
                    f"در {interval_hours} ساعت گذشته، خلاصه‌ای از رویدادهای ثبت شده:\n\n"
                    f"{explanation}\n\n{message}"
                )
    except Exception as e:
        logger.error(f"Failed to generate report via LLM: {e}")
        message = (
            f"📊 گزارش امنیتی و منابع انسانی — {report_date}\n\n"
            f"⚠️ خطا در تولید گزارش: {e}"
        )

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

        interval_hours = settings.report_interval_hours
        if interval_hours < 1:
            interval_hours = 24

        trigger = IntervalTrigger(hours=interval_hours)
        self._scheduler.add_job(
            generate_and_send_report,
            trigger=trigger,
            args=[self._settings_manager, self._container],
            id="report_job",
            replace_existing=True,
        )
        logger.info(
            f"Scheduled report job every {interval_hours}h"
        )
