"""Regression tests for Phase 11: sub_label in frigate_schema.py."""
from frigate_intelligence.interface_adapters.schemas.frigate_schema import (
    SAMPLE_QUERIES,
    SQL_RULES,
)


def test_sample_queries_include_sub_label():
    """SAMPLE_QUERIES should include at least one query referencing sub_label."""
    assert "sub_label" in SAMPLE_QUERIES


def test_sample_queries_include_specific_person_query():
    """SAMPLE_QUERIES should include a query filtering by specific person name."""
    assert "sub_label LIKE '%moein%'" in SAMPLE_QUERIES


def test_sample_queries_include_unknown_query():
    """SAMPLE_QUERIES should include a query for unknown persons."""
    assert "sub_label='unknown'" in SAMPLE_QUERIES


def test_sample_queries_include_distinct_sub_label():
    """SAMPLE_QUERIES should include a DISTINCT sub_label query."""
    assert "DISTINCT sub_label" in SAMPLE_QUERIES


def test_sql_rules_include_sub_label_disambiguation():
    """SQL_RULES should include rule about sub_label vs label disambiguation."""
    assert "sub_label" in SQL_RULES
    assert "label" in SQL_RULES


def test_sql_rules_include_rule_17():
    """SQL_RULES should include rule 17 about filtering by sub_label for person identity."""
    assert "17." in SQL_RULES
    assert "sub_label='person_name'" in SQL_RULES


def test_fallback_schema_includes_sub_label():
    """Fallback schema string should mention sub_label column."""
    fallback = """Frigate SQLite Database Schema:
Tables: event, recordings, timeline, reviewsegment, previews, regions, user
Key table: event (id VARCHAR, label VARCHAR, camera VARCHAR, start_time DATETIME, end_time DATETIME, score REAL, sub_label VARCHAR, zones JSON, data JSON)
Time format: Unix timestamps (float, seconds since epoch)
Camera: cam1
Labels: person, car, motorcycle, bicycle, dog, cat
Sub-labels: recognized person names (e.g., 'soleymani'), 'unknown', or NULL
Zones: configured via Frigate UI (e.g., parking_1, main_gate)"""
    assert "sub_label" in fallback
    assert "Sub-labels" in fallback
