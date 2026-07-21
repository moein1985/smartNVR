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
Sub-labels: recognized person names (e.g., 'soleymani'), 'unknown', or NULL
Zones: configured via Frigate UI (e.g., parking_1, main_gate)"""


def get_frigate_zones(frigate_url: str = "http://frigate:5000") -> str:
    """Fetch zone names from Frigate API for LLM context."""
    try:
        config = json.loads(
            urllib.request.urlopen(f"{frigate_url}/api/config", timeout=5).read()
        )
        zones = []
        for cam_name, cam in config.get("cameras", {}).items():
            for zone_name in cam.get("zones", {}):
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
WHERE label='person' AND sub_label='soleymani'
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
WHERE label='person' AND sub_label='soleymani'
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
ORDER BY start_time DESC LIMIT 50;"""


SQL_RULES = """1. Generate ONLY SELECT queries. No INSERT, UPDATE, DELETE, DROP, ALTER, or ATTACH.
2. Use SQLite syntax (json_extract for JSON fields).
3. CRITICAL: Database time columns (start_time, end_time, timestamp) are stored as Unix timestamps (float). Whenever you SELECT these columns for the final answer, you MUST format them using datetime(column_name, 'unixepoch', 'localtime'). Never return raw unix timestamps to the user.
4. CRITICAL: The standalone `score` and `top_score` columns are often NULL in Frigate 0.18+. To analyze or retrieve detection confidence scores, you MUST use SQLite's JSON functions to extract from the `data` column: json_extract(data, '$.score'). Do NOT use the `score` column directly.
5. Limit results to 100 rows maximum (add LIMIT 100).
6. Table names: event, recordings, timeline, reviewsegment, previews, regions, user.
7. Do not use markdown code fences in output. Return raw SQL only.
8. If a query returns NULL or 0 rows, do NOT conclude that no data exists. The column itself may be unused. Consider alternative columns or JSON extraction.
9. For 'today' filters use: start_time >= strftime('%s', 'now', 'start of day').
10. For 'last hour' filters use: start_time >= strftime('%s', 'now') - 3600.
11. CRITICAL: If the user asks about specific events, recent detections, or asks to 'see' or 'show' something, you MUST include the event `id` column in your SELECT statement. The frontend uses this `id` to render snapshot images. Example: SELECT id, camera, datetime(start_time, 'unixepoch', 'localtime') as time FROM event WHERE label='person' ORDER BY start_time DESC LIMIT 10;
12. The `zones` column is a JSON array (e.g., ["parking_1"]). Use `LIKE '%zone_name%'` for simple filtering or `EXISTS (SELECT 1 FROM json_each(zones) WHERE value='zone_name')` for precise matching.
13. Available detection labels: person, car, motorcycle, bicycle, dog, cat.
14. Available zones: parking_1, main_gate (defined in Frigate config). If the user mentions a zone by description (e.g., "parking area"), map it to the closest zone name.
15. The `recordings` table has `path`, `start_time`, `end_time`, `duration` for 10-second MP4 segments stored at /media/frigate/recordings/YYYY-MM-DD/HH/<camera>/MM.SS.mp4.
16. CRITICAL: The `sub_label` column contains the recognized person's name when facial recognition is active. Values can be a single name (e.g., 'soleymani'), comma-separated names for multiple faces (e.g., 'soleymani, ahmad'), 'unknown' for unrecognized faces, or NULL if no facial recognition was performed.
17. When the user asks about a specific person by name (e.g., "Was soleymani at his desk?"), you MUST filter on `sub_label='person_name'` in addition to `label='person'`. Do NOT search by the `label` column alone — `label` only contains the object class ('person'), not the identity.
18. When the user asks "who was seen" or "who came today", query `SELECT DISTINCT sub_label FROM event WHERE label='person' AND sub_label IS NOT NULL`.
19. When the user asks about "unknown" or "unrecognized" people, filter on `sub_label='unknown'`.
20. The `sub_label` may contain comma-separated values for multiple faces. Use `LIKE '%person_name%'` for flexible matching, or exact match `sub_label='person_name'` for single-face events."""
