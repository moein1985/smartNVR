"""Regression tests for Phase 16.6 — Working Hours & LLM Intelligence.

Tests:
  test_feat_016_6_working_hours_in_prompt
  test_feat_016_6_working_hours_in_schema_context
  test_feat_016_6_zone_name_correlation_hint
  test_feat_016_6_prompt_includes_working_hours
  test_feat_016_6_sample_queries_contain_working_hours
  test_feat_016_6_sql_rules_contain_working_hours_filtering
"""

from frigate_intelligence.interface_adapters.schemas.frigate_schema import (
    load_schema_context,
    SAMPLE_QUERIES,
    SQL_RULES,
)
from frigate_intelligence.use_cases.text_to_sql.prompt_builder import PromptBuilder
from frigate_intelligence.infrastructure.scheduler.report_scheduler import (
    _build_dynamic_prompt,
)
from frigate_intelligence.domain.models.report_rule import ReportRule
from frigate_intelligence.domain.models.settings_model import SettingsModel


def test_feat_016_6_working_hours_in_schema_context():
    """load_schema_context injects working hours when provided."""
    schema = load_schema_context(
        work_hours_start="08:00",
        work_hours_end="16:00",
    )
    assert "Working Hours Context" in schema
    assert "08:00" in schema
    assert "16:00" in schema
    assert "filter events between" in schema


def test_feat_016_6_schema_context_without_working_hours():
    """load_schema_context does not inject working hours when not provided."""
    schema = load_schema_context()
    assert "Working Hours Context" not in schema


def test_feat_016_6_zone_name_correlation_hint():
    """load_schema_context includes zone-name to person correlation rule."""
    schema = load_schema_context(
        work_hours_start="08:00",
        work_hours_end="16:00",
    )
    assert "_table" in schema
    assert "correlate" in schema.lower()
    assert "ahmad_table" in schema
    assert "sub_label" in schema


def test_feat_016_6_prompt_includes_working_hours():
    """PromptBuilder.build injects working hours into schema_text."""
    ctx = PromptBuilder.build(
        work_hours_start="09:00",
        work_hours_end="17:00",
    )
    assert "Working Hours Context" in ctx.schema_text
    assert "09:00" in ctx.schema_text
    assert "17:00" in ctx.schema_text


def test_feat_016_6_prompt_without_working_hours():
    """PromptBuilder.build without work hours does not include the context block."""
    ctx = PromptBuilder.build()
    assert "Working Hours Context" not in ctx.schema_text


def test_feat_016_6_dynamic_prompt_includes_working_hours():
    """_build_dynamic_prompt appends working hours from settings."""
    rule = ReportRule(
        id="test-1",
        name="Test Rule",
        enabled=True,
        zones=["ahmad_table"],
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
    settings = SettingsModel(
        work_hours_start="08:00",
        work_hours_end="16:00",
    )
    prompt = _build_dynamic_prompt(rule, settings)
    assert "08:00" in prompt
    assert "16:00" in prompt
    assert "working hours" in prompt.lower() or "Working hours" in prompt


def test_feat_016_6_sample_queries_contain_working_hours():
    """SAMPLE_QUERIES includes working-hours examples."""
    assert "working hours" in SAMPLE_QUERIES.lower()
    assert "08:00" in SAMPLE_QUERIES or "8 hours" in SAMPLE_QUERIES
    assert "16 hours" in SAMPLE_QUERIES or "16:00" in SAMPLE_QUERIES


def test_feat_016_6_sql_rules_contain_working_hours_filtering():
    """SQL_RULES includes working hours filtering and zone correlation rules."""
    assert "Working Hours Filtering" in SQL_RULES
    assert "Zone-Name to Person Correlation" in SQL_RULES
    assert "work_hours_start" in SQL_RULES
    assert "work_hours_end" in SQL_RULES
    assert "ahmad_table" in SQL_RULES
