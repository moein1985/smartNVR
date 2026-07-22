"""Regression tests for BUG-031/BUG-034: CronService scheduler and Telegram report generation."""
import json
from unittest.mock import MagicMock

from apscheduler.triggers.interval import IntervalTrigger

from frigate_intelligence.config.dependencies import Container
from frigate_intelligence.domain.models.settings_model import SettingsModel
from frigate_intelligence.infrastructure.config.settings_manager import (
    SettingsManager,
)
from frigate_intelligence.infrastructure.scheduler.cron_service import (
    CronService,
    _build_report_prompt,
    _format_report,
)
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLResponse,
)
from frigate_intelligence.domain.entities.query_result import QueryResult


def test_bug_034_build_report_prompt_includes_interval():
    """_build_report_prompt should include the interval hours in the prompt."""
    prompt = _build_report_prompt(6)
    assert "past 6 hours" in prompt
    prompt_24 = _build_report_prompt(24)
    assert "past 24 hours" in prompt_24


def test_bug_034_cron_uses_interval_trigger():
    """CronService should schedule job with IntervalTrigger based on report_interval_hours."""
    settings = SettingsModel(
        telegram_enabled=True,
        telegram_bot_token="test_token",
        telegram_chat_id="test_chat",
        report_interval_hours=6,
        report_timezone="Asia/Tehran",
    )

    settings_manager = MagicMock(spec=SettingsManager)
    settings_manager.load.return_value = settings

    container = MagicMock(spec=Container)
    cron = CronService(settings_manager=settings_manager, container=container)
    cron._refresh_job()

    job = cron._scheduler.get_job("report_job")
    assert job is not None

    trigger = job.trigger
    assert isinstance(trigger, IntervalTrigger)


def test_bug_031_cron_disabled_when_telegram_off():
    """CronService should not schedule a job when telegram_enabled is False."""
    settings = SettingsModel(telegram_enabled=False)
    settings_manager = MagicMock(spec=SettingsManager)
    settings_manager.load.return_value = settings

    cron = CronService(settings_manager=settings_manager)
    cron._refresh_job()

    assert cron._scheduler.get_job("report_job") is None


def test_bug_031_report_formats_zero_events():
    """_format_report should return a Persian fallback message when there are 0 rows."""
    response = TextToSQLResponse(
        question="test",
        sql="SELECT * FROM event",
        result=QueryResult(
            sql="SELECT * FROM event",
            columns=[],
            rows=[],
            row_count=0,
        ),
        explanation="No data",
        attempts=1,
        intent="event_query",
        playback_intent=None,
    )

    report = _format_report(response, "2026-07-22", 24)
    assert "هیچ فعالیت" in report
    assert "2026-07-22" in report


def test_bug_031_report_formats_table_events():
    """_format_report should format workstation events with hours."""
    response = TextToSQLResponse(
        question="test",
        sql="SELECT sub_label, zones, first_seen, last_seen, total_minutes FROM event",
        result=QueryResult(
            sql="SELECT sub_label, zones, first_seen, last_seen, total_minutes FROM event",
            columns=["sub_label", "zones", "first_seen", "last_seen", "total_minutes"],
            rows=[("moein", '["moein_table"]', "09:00", "17:00", "480.0")],
            row_count=1,
        ),
        explanation="Found",
        attempts=1,
        intent="event_query",
        playback_intent=None,
    )

    report = _format_report(response, "2026-07-22", 24)
    assert "فعالیت در ایستگاه‌های کاری" in report
    assert "moein" in report
    assert "moein_table" in report
    assert "~8.0" in report


def test_bug_031_report_formats_sensitive_events():
    """_format_report should format sensitive zone alerts."""
    response = TextToSQLResponse(
        question="test",
        sql="SELECT zones, sub_label, start_time, camera FROM event",
        result=QueryResult(
            sql="SELECT zones, sub_label, start_time, camera FROM event",
            columns=["zones", "sub_label", "start_time", "camera"],
            rows=[('["warehouse_sensitive"]', "unknown", "14:22", "cam1")],
            row_count=1,
        ),
        explanation="Found",
        attempts=1,
        intent="event_query",
        playback_intent=None,
    )

    report = _format_report(response, "2026-07-22", 24)
    assert "هشدارهای مناطق حساس" in report
    assert "warehouse_sensitive" in report
    assert "unknown" in report
    assert "1 هشدار امنیتی" in report


def test_bug_034_settings_model_has_interval_field():
    """SettingsModel should include report_interval_hours with default 24."""
    settings = SettingsModel()
    assert settings.report_interval_hours == 24
    assert settings.report_timezone == "Asia/Tehran"


def test_bug_034_settings_model_serialization():
    """SettingsModel should serialize report_interval_hours to JSON and back."""
    settings = SettingsModel(
        report_interval_hours=6,
        report_timezone="Europe/London",
    )
    raw = settings.model_dump_json()
    data = json.loads(raw)
    assert data["report_interval_hours"] == 6
    assert data["report_timezone"] == "Europe/London"

    restored = SettingsModel(**data)
    assert restored.report_interval_hours == 6
    assert restored.report_timezone == "Europe/London"
