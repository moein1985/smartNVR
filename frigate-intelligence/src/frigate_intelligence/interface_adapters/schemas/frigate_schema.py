import json
import logging
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

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
Key table: event (id VARCHAR, label VARCHAR, camera VARCHAR, start_time DATETIME, end_time DATETIME, score REAL, sub_label VARCHAR, zones JSON, data JSON)
Time format: Unix timestamps (float, seconds since epoch)
Camera: cam1
Labels: person, car, motorcycle, bicycle, dog, cat
Sub-labels: recognized person names (e.g., 'moein'), 'unknown', or NULL
Zones: configured via Frigate UI. Zone naming convention:
- [name]_table: employee workstation (e.g., soleymani_table)
- [name]_sensitive: secure/restricted area (e.g., warehouse_sensitive)"""


def get_frigate_zones(frigate_url: str = "http://192.168.85.203:5000") -> str:
    """Fetch zone names from Frigate API for LLM context, annotated with type."""
    try:
        config = json.loads(
            urllib.request.urlopen(f"{frigate_url}/api/config", timeout=5).read()
        )
        zones = []
        for cam_name, cam in config.get("cameras", {}).items():
            for zone_name in cam.get("zones", {}):
                if zone_name.endswith("_table"):
                    zones.append(f"{zone_name} (camera: {cam_name}, type: workstation)")
                elif zone_name.endswith("_sensitive"):
                    zones.append(f"{zone_name} (camera: {cam_name}, type: restricted)")
                else:
                    zones.append(f"{zone_name} (camera: {cam_name})")
        if zones:
            return "Available zones: " + ", ".join(zones)
    except Exception as e:
        logger.debug(f"Could not fetch zones from Frigate API: {e}")
    return "Available zones: (none configured yet — ask user to define zones in Frigate UI)"


SAMPLE_QUERIES = """-- Get latest person detections (timestamps formatted for readability)
SELECT id, label, datetime(start_time, 'unixepoch', 'localtime') as start_time, datetime(end_time, 'unixepoch', 'localtime') as end_time, json_extract(data, '$.score') as score FROM event WHERE label='person' ORDER BY start_time DESC LIMIT 10;

-- Count detections by label
SELECT label, COUNT(*) as count FROM event GROUP BY label;

-- Average detection score (extract from data JSON, NOT score column)
SELECT AVG(json_extract(data, '$.score')) as avg_score FROM event WHERE label='person';

-- Get recordings with objects
SELECT id, camera, path, datetime(start_time, 'unixepoch', 'localtime') as start_time, duration, objects, motion FROM recordings WHERE objects > 0 ORDER BY start_time DESC;

-- Events in time range (with id for snapshots and formatted timestamps)
SELECT id, label, camera, datetime(start_time, 'unixepoch', 'localtime') as start_time FROM event WHERE start_time BETWEEN 1784377610 AND 1784386200 ORDER BY start_time DESC;

-- Peak hour for detections
SELECT strftime('%H', start_time, 'unixepoch') as hour, COUNT(*) as count FROM event GROUP BY hour ORDER BY count DESC LIMIT 10;

-- Timeline for specific event
SELECT datetime(timestamp, 'unixepoch', 'localtime') as timestamp, class_type, data FROM timeline WHERE source_id='1784386154.716448-7wjons' ORDER BY timestamp ASC;

-- Count cars in a specific zone (using LIKE for simplicity)
SELECT COUNT(*) as count FROM event WHERE label='car' AND zones LIKE '%parking_1%';

-- Events by zone and label in last 24 hours
SELECT label, zones, COUNT(*) as count FROM event
WHERE start_time > strftime('%s','now','-1 day')
GROUP BY label, zones;

-- Zone entry events using json_each (precise zone matching)
SELECT id, label, camera, datetime(start_time, 'unixepoch', 'localtime') as start
FROM event
WHERE EXISTS (SELECT 1 FROM json_each(zones) WHERE value='main_gate')
ORDER BY start_time DESC LIMIT 50;

-- Detections by camera and label with zone info
SELECT camera, label, zones, COUNT(*) as count, MAX(json_extract(data, '$.score')) as max_score
FROM event
WHERE start_time > strftime('%s','now','-7 days')
GROUP BY camera, label, zones
ORDER BY count DESC;

-- Hourly detection count by label
SELECT label, strftime('%H', datetime(start_time, 'unixepoch', 'localtime')) as hour, COUNT(*) as count
FROM event
WHERE start_time > strftime('%s','now','-1 day')
GROUP BY label, hour
ORDER BY hour;

-- Find events where a specific person was recognized
SELECT id, label, sub_label, camera, datetime(start_time, 'unixepoch', 'localtime') as start_time
FROM event
WHERE label='person' AND sub_label LIKE '%moein%'
ORDER BY start_time DESC LIMIT 50;

-- Find all recognized persons in the last 24 hours
SELECT sub_label, COUNT(*) as appearances,
       datetime(MIN(start_time), 'unixepoch', 'localtime') as first_seen,
       datetime(MAX(start_time), 'unixepoch', 'localtime') as last_seen
FROM event
WHERE label='person' AND sub_label IS NOT NULL
  AND start_time >= strftime('%s', 'now', '-1 day')
GROUP BY sub_label
ORDER BY appearances DESC;

-- Check if a specific person was seen in a time range
SELECT id, camera, datetime(start_time, 'unixepoch', 'localtime') as start_time,
       datetime(end_time, 'unixepoch', 'localtime') as end_time
FROM event
WHERE label='person' AND sub_label LIKE '%moein%'
  AND start_time BETWEEN strftime('%s', 'now', 'start of day', '-1 day')
                     AND strftime('%s', 'now', 'start of day')
ORDER BY start_time ASC;

-- List all unique recognized persons
SELECT DISTINCT sub_label FROM event
WHERE label='person' AND sub_label IS NOT NULL
ORDER BY sub_label;

-- Find unknown persons (detected but not recognized)
SELECT id, camera, datetime(start_time, 'unixepoch', 'localtime') as start_time
FROM event
WHERE label='person' AND sub_label='unknown'
  AND start_time >= strftime('%s', 'now', '-1 day')
ORDER BY start_time DESC LIMIT 50;

-- Who was at Soleymani's desk today (excluding Soleymani)?
SELECT id, sub_label, datetime(start_time, 'unixepoch', 'localtime') as start_time,
       datetime(end_time, 'unixepoch', 'localtime') as end_time
FROM event
WHERE zones LIKE '%soleymani_table%' AND label='person'
  AND sub_label NOT LIKE '%soleymani%'
  AND start_time >= strftime('%s', 'now', 'start of day')
ORDER BY start_time DESC;

-- Soleymani's work hours today (first seen, last seen, total duration)
SELECT sub_label,
       datetime(MIN(start_time), 'unixepoch', 'localtime') as first_seen,
       datetime(MAX(end_time), 'unixepoch', 'localtime') as last_seen,
       ROUND(SUM(end_time - start_time) / 60, 1) as total_minutes
FROM event
WHERE zones LIKE '%soleymani_table%' AND sub_label LIKE '%soleymani%'
  AND start_time >= strftime('%s', 'now', 'start of day')
GROUP BY sub_label;

-- Security alerts for sensitive zones today
SELECT id, camera, zones, sub_label,
       datetime(start_time, 'unixepoch', 'localtime') as start_time
FROM event
WHERE zones LIKE '%_sensitive%' AND label='person'
  AND start_time >= strftime('%s', 'now', 'start of day')
ORDER BY start_time DESC;

-- Daily summary: all _table zone activity grouped by person
SELECT sub_label, zones,
       datetime(MIN(start_time), 'unixepoch', 'localtime') as first_seen,
       datetime(MAX(end_time), 'unixepoch', 'localtime') as last_seen,
       COUNT(*) as event_count
FROM event
WHERE zones LIKE '%_table%' AND label='person' AND sub_label IS NOT NULL
  AND start_time >= strftime('%s', 'now', 'start of day')
GROUP BY sub_label, zones
ORDER BY zones, first_seen;"""


SQL_RULES = """1. Generate ONLY SELECT queries. No INSERT, UPDATE, DELETE, DROP, ALTER, or ATTACH.
2. Use SQLite syntax (json_extract for JSON fields).
3. Time columns (start_time, end_time, timestamp) are Unix timestamps (float). When SELECTing for display, format with datetime(column, 'unixepoch', 'localtime'). Never return raw timestamps.
4. The `score` and `top_score` columns are often NULL. To get detection confidence, use json_extract(data, '$.score') instead.
5. Limit results to 100 rows (LIMIT 100).
6. Tables: event, recordings, timeline, reviewsegment, previews, regions, user.
7. Return raw SQL only — no markdown code fences.
8. If a column returns NULL or 0 rows, consider alternative columns or JSON extraction before concluding no data exists.
9. For 'today': start_time >= strftime('%s', 'now', 'start of day'). For 'last hour': start_time >= strftime('%s', 'now') - 3600.
10. The `zones` column is a JSON array. Use LIKE '%zone_name%' for simple filtering or EXISTS (SELECT 1 FROM json_each(zones) WHERE value='zone_name') for precise matching.
11. Detection labels: person, car, motorcycle, bicycle, dog, cat. Zones: parking_1, main_gate.
12. The `recordings` table has path, start_time, end_time, duration for 10-second MP4 segments at /media/frigate/recordings/YYYY-MM-DD/HH/<camera>/MM.SS.mp4.
13. The `sub_label` column stores recognized person names (e.g., 'moein', 'ahmad'), 'unknown' for unrecognized faces, comma-separated for multiple faces, or NULL. When a user asks about a person by name, filter with sub_label LIKE '%name%' alongside label='person'. Never use label='person_name'. For "who was seen", query DISTINCT sub_label WHERE sub_label IS NOT NULL.
14. Zone Naming Convention: Zones ending with `_table` (e.g., `soleymani_table`) represent employee workstations. Zones ending with `_sensitive` (e.g., `warehouse_sensitive`) represent secure/restricted areas. When a user asks about "desk presence", "work hours", or "who was at X's desk", filter zones LIKE '%_table'. When asking about "unauthorized access", "security alerts", or "restricted areas", filter zones LIKE '%_sensitive'.
15. Zone + sub_label Synergy: To find "who was at Soleymani's desk", combine zone and sub_label: WHERE zones LIKE '%soleymani_table%' AND sub_label NOT LIKE '%soleymani%' AND label='person'. This identifies anyone OTHER than Soleymani at their desk. To find Soleymani's active hours: WHERE zones LIKE '%soleymani_table%' AND sub_label LIKE '%soleymani%'.
16. Work Hours Calculation: To calculate active desk time for an employee, query events in their `_table` zone with their `sub_label`, then compute SUM(end_time - start_time) for overlapping or consecutive events. Use MIN(start_time) as first_seen and MAX(end_time) as last_seen for daily presence summary."""
