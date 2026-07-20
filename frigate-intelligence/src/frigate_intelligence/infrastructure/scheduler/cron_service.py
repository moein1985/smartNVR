import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from frigate_intelligence.domain.models.settings_model import SettingsModel
from frigate_intelligence.infrastructure.config.settings_manager import (
    SettingsManager,
)

logger = logging.getLogger(__name__)

_FREQUENCY_CRON_MAP: dict[str, str] = {
    "daily_8am": "0 8 * * *",
    "daily_8pm": "0 20 * * *",
    "weekly": "0 8 * * 0",
}


async def generate_and_send_report(
    settings_manager: SettingsManager,
) -> None:
    settings: SettingsModel = settings_manager.load()
    target = settings.report_target
    logger.info(
        f"Generating report for [{target}] based on Cron schedule"
    )


class CronService:
    def __init__(self, settings_manager: SettingsManager) -> None:
        self._settings_manager = settings_manager
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self._refresh_job()
        self._scheduler.start()
        logger.info("Cron scheduler started")

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Cron scheduler stopped")

    def _refresh_job(self) -> None:
        from apscheduler.triggers.cron import CronTrigger

        settings = self._settings_manager.load()
        frequency = settings.report_frequency

        existing = self._scheduler.get_job("report_job")
        if existing:
            self._scheduler.remove_job("report_job")

        if frequency == "disabled":
            logger.info("Cron reporting is disabled, no job scheduled")
            return

        cron_expr = _FREQUENCY_CRON_MAP.get(frequency)
        if not cron_expr:
            logger.warning(f"Unknown frequency '{frequency}', skipping")
            return

        trigger = CronTrigger.from_crontab(cron_expr)
        self._scheduler.add_job(
            generate_and_send_report,
            trigger=trigger,
            args=[self._settings_manager],
            id="report_job",
            replace_existing=True,
        )
        logger.info(f"Scheduled report job with frequency '{frequency}'")
