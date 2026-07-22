"""Regression tests for BUG-031: CronService scheduler and Telegram report generation."""
import json
from unittest.mock import MagicMock

from apscheduler.triggers.cron import CronTrigger

from frigate_intelligence.config.dependencies import Container
from frigate_intelligence.domain.models.settings_model import SettingsModel
from frigate_intelligence.infrastructure.config.settings_manager import (
    SettingsManager,
)
from frigate_intelligence.infrastructure.scheduler.cron_service import (
    CronService,
    _parse_report_time,
    _format_report,
)
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLResponse,
)
from frigate_intelligence.domain.entities.query_result import QueryResult


def test_bug_031_parse_report_time_valid():
    """_parse_report_time should correctly parse HH:MM format."""
    assert _parse_report_time("21:00") == (21, 0)
    assert _parse_report_time("08:30") == (8, 30)
    assert _parse_report_time("00:15") == (0, 15)


def test_bug_031_parse_report_time_invalid():
    """_parse_report_time should fall back to 21:00 for invalid input."""
    assert _parse_report_time("invalid") == (21, 0)
    assert _parse_report_time("") == (21, 0)
    assert _parse_report_time("25:99") == (25, 99)


def test_bug_031_cron_parses_report_time():
    """CronService should schedule job at the correct hour/minute with timezone."""
    settings = SettingsModel(
        telegram_enabled=True,
        telegram_bot_token="test_token",
        telegram_chat_id="test_chat",
        report_time="21:00",
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
    assert isinstance(trigger, CronTrigger)
    assert str(trigger.timezone) == "Asia/Tehran"

    fields = {f.name: str(f) for f in trigger.fields}
    assert fields["hour"] == "21"
    assert fields["minute"] == "0"


def test_bug_031_cron_disabled_when_telegram_off():
    """CronService should not schedule a job when telegram_enabled is False."""
    settings = SettingsModel(telegram_enabled=False)
    settings_manager = MagicMock(spec=SettingsManager)
    settings_manager.load.return_value = settings

    cron = CronService(settings_manager=settings_manager)
    cron._refresh_job()

    assert cron._scheduler.get_job("report_job") is None


def test_bug_031_report_formats_zero_events():
    """_format_report should return a fallback message when there are 0 rows."""
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

    report = _format_report(response, "2026-07-22")
    assert "No activity detected" in report
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

    report = _format_report(response, "2026-07-22")
    assert "Workstation Activity" in report
    assert "moein" in report
    assert "moein_table" in report
    assert "~8.0h" in report


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

    report = _format_report(response, "2026-07-22")
    assert "Restricted Area Alerts" in report
    assert "warehouse_sensitive" in report
    assert "unknown" in report
    assert "1 security alerts" in report


def test_bug_031_settings_model_has_new_fields():
    """SettingsModel should include report_time and report_timezone with defaults."""
    settings = SettingsModel()
    assert settings.report_time == "21:00"
    assert settings.report_timezone == "Asia/Tehran"


def test_bug_031_settings_model_serialization():
    """SettingsModel should serialize new fields to JSON and back."""
    settings = SettingsModel(
        report_time="18:30",
        report_timezone="Europe/London",
    )
    raw = settings.model_dump_json()
    data = json.loads(raw)
    assert data["report_time"] == "18:30"
    assert data["report_timezone"] == "Europe/London"

    restored = SettingsModel(**data)
    assert restored.report_time == "18:30"
    assert restored.report_timezone == "Europe/London"
