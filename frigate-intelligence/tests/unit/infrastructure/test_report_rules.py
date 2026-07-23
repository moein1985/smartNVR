"""Regression tests for Phase 16.2 — Report Rules Engine & History.

Tests: test_feat_016_2_rule_crud_create, test_feat_016_2_rule_crud_update,
       test_feat_016_2_rule_crud_delete, test_feat_016_2_scheduler_multi_job,
       test_feat_016_2_prompt_generation_zones, test_feat_016_2_prompt_generation_working_hours,
       test_feat_016_2_history_fifo_eviction, test_feat_016_2_notifier_factory_telegram,
       test_feat_016_2_notifier_factory_bale, test_feat_016_2_bale_notifier_structure
"""

import asyncio

import pytest

from frigate_intelligence.domain.models.report_rule import ReportRule
from frigate_intelligence.domain.models.settings_model import SettingsModel
from frigate_intelligence.infrastructure.config.report_rule_manager import (
    ReportRuleManager,
)
from frigate_intelligence.infrastructure.config.report_history_manager import (
    ReportHistoryManager,
)
from frigate_intelligence.infrastructure.notifiers.notifier_factory import (
    NotifierFactory,
)
from frigate_intelligence.infrastructure.notifiers.bale_notifier import BaleNotifier
from frigate_intelligence.infrastructure.notifiers.telegram_notifier import (
    TelegramNotifier,
)
from frigate_intelligence.infrastructure.scheduler.report_scheduler import (
    _build_dynamic_prompt,
    ReportScheduler,
)


@pytest.fixture
def temp_rule_manager(tmp_path):
    return ReportRuleManager(file_path=str(tmp_path / "report_rules.json"))


@pytest.fixture
def temp_history_manager(tmp_path):
    return ReportHistoryManager(file_path=str(tmp_path / "report_history.json"))


def _make_rule(
    name: str = "Test Rule",
    zones: list[str] | None = None,
    enabled: bool = True,
) -> ReportRule:
    return ReportRule(
        id="",
        name=name,
        enabled=enabled,
        zones=zones or [],
        cameras=["cam1"],
        labels=["person"],
        interval_hours=24,
        timezone="Asia/Tehran",
        destination="telegram",
        chat_id="",
        prompt_template="",
        include_summary=True,
        include_raw_data=False,
    )


# ─── ReportRuleManager CRUD tests ───


def test_feat_016_2_rule_crud_create(temp_rule_manager):
    """Creating a report rule works."""
    rule = _make_rule("Daily Report", zones=["ahmad_table"])
    created = temp_rule_manager.create_rule(rule)
    assert created.id != ""
    assert created.name == "Daily Report"
    assert created.zones == ["ahmad_table"]
    assert created.created_at != ""

    fetched = temp_rule_manager.get_by_id(created.id)
    assert fetched is not None
    assert fetched.name == "Daily Report"


def test_feat_016_2_rule_crud_update(temp_rule_manager):
    """Updating a report rule works."""
    rule = _make_rule("Weekly Report")
    created = temp_rule_manager.create_rule(rule)

    updated = temp_rule_manager.update_rule(
        created.id,
        {"name": "Bi-Weekly Report", "interval_hours": 12},
    )
    assert updated.name == "Bi-Weekly Report"
    assert updated.interval_hours == 12


def test_feat_016_2_rule_crud_delete(temp_rule_manager):
    """Deleting a report rule works."""
    rule = _make_rule("Temp Rule")
    created = temp_rule_manager.create_rule(rule)

    result = temp_rule_manager.delete_rule(created.id)
    assert result is True
    assert temp_rule_manager.get_by_id(created.id) is None


def test_feat_016_2_rule_crud_delete_not_found(temp_rule_manager):
    """Deleting a non-existent rule raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        temp_rule_manager.delete_rule("nonexistent")


# ─── ReportHistoryManager FIFO tests ───


def test_feat_016_2_history_fifo_eviction(temp_history_manager):
    """History manager evicts oldest entries beyond 100."""
    for i in range(105):
        temp_history_manager.add_entry(
            rule_id="rule1",
            rule_name=f"Rule {i}",
            status="success",
            message_preview=f"Message {i}",
        )

    assert temp_history_manager.count() == 100

    entries = temp_history_manager.list_entries(limit=100)
    assert entries[0].rule_name == "Rule 104"
    assert entries[-1].rule_name == "Rule 5"


def test_feat_016_2_history_by_rule(temp_history_manager):
    """Filtering history by rule_id works."""
    temp_history_manager.add_entry("rule1", "Rule 1", "success")
    temp_history_manager.add_entry("rule2", "Rule 2", "error")
    temp_history_manager.add_entry("rule1", "Rule 1", "success")

    entries = temp_history_manager.list_by_rule("rule1")
    assert len(entries) == 2
    assert all(e.rule_id == "rule1" for e in entries)


# ─── Prompt generation tests ───


def test_feat_016_2_prompt_generation_zones():
    """Dynamic prompt includes zone hints with suffix logic."""
    rule = _make_rule(zones=["ahmad_table", "vault_sensitive"])
    settings = SettingsModel()

    prompt = _build_dynamic_prompt(rule, settings)

    assert "ahmad_table" in prompt
    assert "tracks person 'ahmad'" in prompt
    assert "vault_sensitive" in prompt
    assert "sensitive/security area" in prompt


def test_feat_016_2_prompt_generation_working_hours():
    """Dynamic prompt includes working hours context."""
    rule = _make_rule()
    settings = SettingsModel(work_hours_start="09:00", work_hours_end="17:00")

    prompt = _build_dynamic_prompt(rule, settings)

    assert "09:00" in prompt
    assert "17:00" in prompt
    assert "working hours" in prompt.lower()


def test_feat_016_2_prompt_generation_custom_template():
    """Custom prompt template is used when provided."""
    rule = _make_rule()
    rule.prompt_template = "Show me all events in the last {interval} hours"
    settings = SettingsModel()

    prompt = _build_dynamic_prompt(rule, settings)

    assert "Show me all events" in prompt
    assert "working hours" in prompt.lower()


# ─── NotifierFactory tests ───


def test_feat_016_2_notifier_factory_telegram():
    """NotifierFactory creates TelegramNotifier for telegram destination."""
    factory = NotifierFactory(
        telegram_bot_token="test_token",
        telegram_chat_id="123",
    )
    notifier = factory.create("telegram")
    assert isinstance(notifier, TelegramNotifier)


def test_feat_016_2_notifier_factory_bale():
    """NotifierFactory creates BaleNotifier for bale destination."""
    factory = NotifierFactory(
        bale_bot_token="bale_token",
        bale_chat_id="456",
    )
    notifier = factory.create("bale")
    assert isinstance(notifier, BaleNotifier)


def test_feat_016_2_notifier_factory_unknown_defaults_telegram():
    """Unknown destination defaults to Telegram."""
    factory = NotifierFactory(
        telegram_bot_token="test_token",
        telegram_chat_id="123",
    )
    notifier = factory.create("unknown")
    assert isinstance(notifier, TelegramNotifier)


# ─── BaleNotifier structure test ───


def test_feat_016_2_bale_notifier_structure():
    """BaleNotifier has correct API URL structure."""
    notifier = BaleNotifier(
        bot_token="test_bale_token",
        default_chat_id="test_chat",
    )
    assert notifier._token == "test_bale_token"
    assert notifier._default_chat_id == "test_chat"
    assert "api.bale.ai/v1/bots/test_bale_token" in notifier._base_url


# ─── ReportScheduler multi-job test ───


@pytest.mark.asyncio
async def test_feat_016_2_scheduler_multi_job(temp_rule_manager, temp_history_manager):
    """ReportScheduler schedules multiple jobs for multiple enabled rules."""
    from frigate_intelligence.infrastructure.config.settings_manager import (
        SettingsManager,
    )

    rule1 = _make_rule("Rule 1", zones=["zone_a"])
    rule2 = _make_rule("Rule 2", zones=["zone_b"])
    temp_rule_manager.create_rule(rule1)
    temp_rule_manager.create_rule(rule2)

    settings_manager = SettingsManager()
    scheduler = ReportScheduler(
        settings_manager=settings_manager,
        rule_manager=temp_rule_manager,
        history_manager=temp_history_manager,
        container=None,
    )

    scheduler.start()

    await asyncio.sleep(0.1)

    job_ids = [job.id for job in scheduler._scheduler.get_jobs()]
    assert len(job_ids) == 2
    assert any("report_rule_" in jid for jid in job_ids)

    scheduler.stop()


@pytest.mark.asyncio
async def test_feat_016_2_scheduler_refresh_rule(temp_rule_manager, temp_history_manager):
    """ReportScheduler refresh_rule reschedules a single rule."""
    from frigate_intelligence.infrastructure.config.settings_manager import (
        SettingsManager,
    )

    rule = _make_rule("Refreshable Rule", enabled=True)
    created = temp_rule_manager.create_rule(rule)

    settings_manager = SettingsManager()
    scheduler = ReportScheduler(
        settings_manager=settings_manager,
        rule_manager=temp_rule_manager,
        history_manager=temp_history_manager,
        container=None,
    )
    scheduler.start()
    await asyncio.sleep(0.1)

    assert len(scheduler._scheduler.get_jobs()) == 1

    temp_rule_manager.update_rule(created.id, {"interval_hours": 6})
    scheduler.refresh_rule(created.id)

    jobs = scheduler._scheduler.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == f"report_rule_{created.id}"

    scheduler.stop()


@pytest.mark.asyncio
async def test_feat_016_2_scheduler_remove_rule(temp_rule_manager, temp_history_manager):
    """ReportScheduler remove_rule removes the job."""
    from frigate_intelligence.infrastructure.config.settings_manager import (
        SettingsManager,
    )

    rule = _make_rule("Removable Rule", enabled=True)
    created = temp_rule_manager.create_rule(rule)

    settings_manager = SettingsManager()
    scheduler = ReportScheduler(
        settings_manager=settings_manager,
        rule_manager=temp_rule_manager,
        history_manager=temp_history_manager,
        container=None,
    )
    scheduler.start()
    await asyncio.sleep(0.1)

    assert len(scheduler._scheduler.get_jobs()) == 1

    scheduler.remove_rule(created.id)

    assert len(scheduler._scheduler.get_jobs()) == 0

    scheduler.stop()


@pytest.mark.asyncio
async def test_feat_016_2_scheduler_disabled_rule_not_scheduled(
    temp_rule_manager, temp_history_manager
):
    """Disabled rules are not scheduled on start."""
    from frigate_intelligence.infrastructure.config.settings_manager import (
        SettingsManager,
    )

    rule = _make_rule("Disabled Rule", enabled=False)
    temp_rule_manager.create_rule(rule)

    settings_manager = SettingsManager()
    scheduler = ReportScheduler(
        settings_manager=settings_manager,
        rule_manager=temp_rule_manager,
        history_manager=temp_history_manager,
        container=None,
    )
    scheduler.start()
    await asyncio.sleep(0.1)

    assert len(scheduler._scheduler.get_jobs()) == 0

    scheduler.stop()
