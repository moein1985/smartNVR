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


SAMPLE_QUERIES = """-- Get latest person detections (timestamps formatted for readability)
SELECT id, label, datetime(start_time, 'unixepoch', 'localtime') as start_time, datetime(end_time, 'unixepoch', 'localtime') as end_time, json_extract(data, '$.score') as score FROM event WHERE label='person' ORDER BY start_time DESC LIMIT 10;

-- Count detections by label
SELECT label, COUNT(*) as count FROM event GROUP BY label;

-- Average detection score (extract from data JSON, NOT score column)
SELECT AVG(json_extract(data, '$.score')) as avg_score FROM event WHERE label='person';

-- Get recordings with objects
SELECT id, camera, path, datetime(start_time, 'unixepoch', 'localtime') as start_time, duration, objects, motion FROM recordings WHERE objects > 0 ORDER BY start_time DESC;

-- Events in time range (with formatted timestamps)
SELECT id, label, camera, datetime(start_time, 'unixepoch', 'localtime') as start_time FROM event WHERE start_time BETWEEN 1784377610 AND 1784386200 ORDER BY start_time DESC;

-- Peak hour for detections
SELECT strftime('%H', start_time, 'unixepoch') as hour, COUNT(*) as count FROM event GROUP BY hour ORDER BY count DESC LIMIT 10;

-- Timeline for specific event
SELECT datetime(timestamp, 'unixepoch', 'localtime') as timestamp, class_type, data FROM timeline WHERE source_id='1784386154.716448-7wjons' ORDER BY timestamp ASC;"""


SQL_RULES = """1. Generate ONLY SELECT queries. No INSERT, UPDATE, DELETE, DROP, ALTER, or ATTACH.
2. Use SQLite syntax (json_extract for JSON fields).
3. CRITICAL: Database time columns (start_time, end_time, timestamp) are stored as Unix timestamps (float). Whenever you SELECT these columns for the final answer, you MUST format them using datetime(column_name, 'unixepoch', 'localtime'). Never return raw unix timestamps to the user.
4. CRITICAL: The standalone `score` and `top_score` columns are often NULL in Frigate 0.18+. To analyze or retrieve detection confidence scores, you MUST use SQLite's JSON functions to extract from the `data` column: json_extract(data, '$.score'). Do NOT use the `score` column directly.
5. Limit results to 100 rows maximum (add LIMIT 100).
6. Table names: event, recordings, timeline, reviewsegment, previews, regions, user.
7. Do not use markdown code fences in output. Return raw SQL only.
8. If a query returns NULL or 0 rows, do NOT conclude that no data exists. The column itself may be unused. Consider alternative columns or JSON extraction.
9. For 'today' filters use: start_time >= strftime('%s', 'now', 'start of day').
10. For 'last hour' filters use: start_time >= strftime('%s', 'now') - 3600."""
