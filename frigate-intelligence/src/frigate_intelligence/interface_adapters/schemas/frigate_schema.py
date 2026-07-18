from pathlib import Path

SCHEMA_REPORT_PATH = (
    Path(__file__).parent.parent.parent.parent.parent.parent
    / "Frigate_Database_Schema_Report.md"
)


def load_schema_context() -> str:
    """Load the Frigate database schema report as a string for LLM context."""
    if SCHEMA_REPORT_PATH.exists():
        return SCHEMA_REPORT_PATH.read_text(encoding="utf-8")
    return """Frigate SQLite Database Schema:
Tables: event, recordings, timeline, reviewsegment, previews, regions, user
Key table: event (id VARCHAR, label VARCHAR, camera VARCHAR, start_time DATETIME, end_time DATETIME, score REAL, zones JSON, data JSON)
Time format: Unix timestamps (float, seconds since epoch)
Camera: cam1
Labels: person"""


SAMPLE_QUERIES = """-- Get latest person detections
SELECT id, label, start_time, end_time, score FROM event WHERE label='person' ORDER BY start_time DESC LIMIT 10;

-- Count detections by label
SELECT label, COUNT(*) as count FROM event GROUP BY label;

-- Get recordings with objects
SELECT id, camera, path, start_time, duration, objects, motion FROM recordings WHERE objects > 0 ORDER BY start_time DESC;

-- Events in time range
SELECT * FROM event WHERE start_time BETWEEN 1784377610 AND 1784386200 ORDER BY start_time DESC;

-- Timeline for specific event
SELECT timestamp, class_type, data FROM timeline WHERE source_id='1784386154.716448-7wjons' ORDER BY timestamp ASC;"""


SQL_RULES = """1. Generate ONLY SELECT queries. No INSERT, UPDATE, DELETE, DROP, ALTER, or ATTACH.
2. Use SQLite syntax (json_extract for JSON fields).
3. Time fields are Unix timestamps (float). Use datetime(column, 'unixepoch') to convert.
4. Limit results to 100 rows maximum (add LIMIT 100).
5. Table names: event, recordings, timeline, reviewsegment, previews, regions, user.
6. Do not use markdown code fences in output. Return raw SQL only."""
