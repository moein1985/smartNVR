"""Regression tests for BUG-030: Zone naming conventions in frigate_schema.py."""
from frigate_intelligence.interface_adapters.schemas.frigate_schema import (
    SAMPLE_QUERIES,
    SQL_RULES,
    get_frigate_zones,
    load_schema_context,
)


def test_bug_030_sql_rules_include_table_convention():
    """SQL_RULES should mention _table zone convention for workstations."""
    assert "_table" in SQL_RULES
    assert "workstation" in SQL_RULES


def test_bug_030_sql_rules_include_sensitive_convention():
    """SQL_RULES should mention _sensitive zone convention for restricted areas."""
    assert "_sensitive" in SQL_RULES
    assert "restricted" in SQL_RULES


def test_bug_030_sql_rules_include_zone_sublabel_synergy():
    """SQL_RULES should include guidance on combining zones with sub_label."""
    assert "soleymani_table" in SQL_RULES
    assert "sub_label NOT LIKE" in SQL_RULES


def test_bug_030_sql_rules_include_work_hours_calculation():
    """SQL_RULES should include guidance on work hours calculation."""
    assert "SUM(end_time - start_time)" in SQL_RULES
    assert "first_seen" in SQL_RULES
    assert "last_seen" in SQL_RULES


def test_bug_030_sample_queries_include_who_at_desk():
    """SAMPLE_QUERIES should include a query for who was at someone's desk (excluding them)."""
    assert "soleymani_table" in SAMPLE_QUERIES
    assert "sub_label NOT LIKE '%soleymani%'" in SAMPLE_QUERIES


def test_bug_030_sample_queries_include_work_hours():
    """SAMPLE_QUERIES should include a query for employee work hours."""
    assert "total_minutes" in SAMPLE_QUERIES
    assert "MIN(start_time)" in SAMPLE_QUERIES
    assert "MAX(end_time)" in SAMPLE_QUERIES


def test_bug_030_sample_queries_include_sensitive_alerts():
    """SAMPLE_QUERIES should include a query for security alerts in sensitive zones."""
    assert "%_sensitive%" in SAMPLE_QUERIES
    assert "label='person'" in SAMPLE_QUERIES


def test_bug_030_sample_queries_include_daily_summary():
    """SAMPLE_QUERIES should include a daily summary query for _table zones."""
    assert "%_table%" in SAMPLE_QUERIES
    assert "event_count" in SAMPLE_QUERIES


def test_bug_030_fallback_schema_includes_zone_conventions():
    """Fallback schema text should mention _table and _sensitive zone conventions."""
    from frigate_intelligence.interface_adapters.schemas import frigate_schema

    original_path = frigate_schema.SCHEMA_REPORT_PATH
    frigate_schema.SCHEMA_REPORT_PATH = frigate_schema.Path("/nonexistent/path")

    try:
        schema = load_schema_context()
        assert "_table" in schema
        assert "_sensitive" in schema
        assert "workstation" in schema
        assert "restricted" in schema
    finally:
        frigate_schema.SCHEMA_REPORT_PATH = original_path


def test_bug_030_get_frigate_zones_uses_correct_url():
    """get_frigate_zones default URL should be the host IP, not 'frigate' hostname."""
    import inspect

    sig = inspect.signature(get_frigate_zones)
    default_url = sig.parameters["frigate_url"].default
    assert "192.168.85.203" in default_url
    assert "frigate:5000" not in default_url
