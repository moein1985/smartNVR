# Frigate Database Schema Report for LLM Text-to-SQL

## Overview

- **Database**: SQLite (`/opt/frigate/config/frigate.db`)
- **Frigate Version**: 0.18.0-5f6043a
- **Camera**: `cam1` (RTSP: `192.168.85.112:554`)
- **Model**: YOLOv9-t-320 (ONNX, GPU: RTX 5050)
- **Extraction Date**: 2026-07-18 14:54 UTC

---

## 1. All Tables

| Table | Rows | Description |
|-------|------|-------------|
| `event` | 83 | Object detection events (person, car, etc.) |
| `recordings` | 736 | Video recording segments with motion/object counts |
| `timeline` | 172 | Timeline of tracking events (enter, update, gone) |
| `reviewsegment` | 15 | Review segments grouping related events |
| `previews` | 3 | Preview thumbnails for recordings |
| `regions` | 1 | Motion detection region grid per camera |
| `migratehistory` | 35 | Database migration history |
| `user` | 1 | User accounts (admin) |
| `export` | 0 | Exported clips |
| `exportcase` | 0 | Export case folders |
| `trigger` | 0 | Custom triggers (audio/object) |
| `userreviewstatus` | 0 | User review status for segments |
| `sqlite_sequence` | 0 | SQLite internal |

---

## 2. EVENT Table (Primary Table for Object Detection)

### Schema

```sql
CREATE TABLE "event" (
    "id" VARCHAR(30) NOT NULL PRIMARY KEY,
    "label" VARCHAR(20) NOT NULL,           -- Object class: "person", "car", etc.
    "camera" VARCHAR(20) NOT NULL,          -- Camera name: "cam1"
    "start_time" DATETIME NOT NULL,         -- Unix timestamp (float), e.g. 1784386154.716448
    "end_time" DATETIME,                    -- Unix timestamp (float), NULL while active
    "top_score" REAL,                       -- Highest detection confidence (0.0-1.0)
    "false_positive" INTEGER,               -- 0 or 1, whether marked as false positive
    "zones" JSON NOT NULL,                  -- JSON array of zone names, e.g. []
    "thumbnail" TEXT,                       -- Thumbnail path (may be NULL)
    "has_clip" INTEGER NOT NULL,            -- 1 if video clip exists, 0 otherwise
    "has_snapshot" INTEGER NOT NULL,        -- 1 if snapshot exists, 0 otherwise
    "region" JSON,                          -- Detection region coordinates
    "box" JSON,                             -- Bounding box [x, y, width, height] normalized 0-1
    "area" INTEGER,                         -- Detection area in pixels
    "retain_indefinitely" INTEGER NOT NULL, -- 1 if retained indefinitely, 0 otherwise
    "sub_label" VARCHAR(100),               -- Sub-label (e.g. bird species), NULL if none
    "ratio" REAL,                           -- Aspect ratio of bounding box
    "plus_id" VARCHAR(30),                  -- Frigate+ model ID, NULL if not Frigate+
    "score" REAL,                           -- Detection confidence score (0.0-1.0)
    "model_hash" VARCHAR(32),               -- MD5 hash of model file
    "detector_type" VARCHAR(32),            -- Detector type: "onnx", "edgetpu", etc.
    "model_type" VARCHAR(32),               -- Model type: "yolo-generic", "yolonas", etc.
    "data" JSON NOT NULL                    -- Additional data: box, label, score, etc.
)
```

### Indexes

| Index Name | Columns |
|------------|---------|
| `event_start_time_end_time` | `start_time, end_time` |
| `event_label_start_time` | `label, start_time` |
| `event_label` | `label` |
| `event_camera` | `camera` |
| `sqlite_autoindex_event_1` | `id` (unique) |

### Sample Data (Latest 5 Events)

| id | label | camera | start_time | end_time | score | detector_type | model_type |
|----|-------|--------|------------|----------|-------|---------------|------------|
| `1784386154.716448-7wjons` | person | cam1 | 1784386154.72 (14:49:14) | 1784386212.16 (14:50:12) | NULL | onnx | yolo-generic |
| `1784386075.168797-6qfg26` | person | cam1 | 1784386075.17 (14:47:55) | 1784386077.17 (14:47:57) | NULL | onnx | yolo-generic |
| `1784386072.168559-pnmxpt` | person | cam1 | 1784386072.17 (14:47:52) | 1784386156.52 (14:49:16) | NULL | onnx | yolo-generic |
| `1784386071.568256-yxsql4` | person | cam1 | 1784386071.57 (14:47:51) | 1784386072.77 (14:47:52) | NULL | onnx | yolo-generic |
| `1784381975.454224-f3vsr9` | person | cam1 | 1784381975.45 (13:39:35) | 1784381987.85 (13:39:47) | NULL | onnx | yolo-generic |

### Event Statistics

- **Total events**: 83
- **Labels**: `person` (83)
- **Cameras**: `cam1` (83)
- **Time range**: 2026-07-18 12:26:50 → 2026-07-18 14:49:14

### `data` JSON Field Structure

```json
{
    "box": [0.7875, 0.302, 0.159, 0.43],  // [x, y, width, height] normalized 0-1
    "label": "person",
    "score": 0.85,
    "region": [0.1, 0.1, 0.5, 0.5]        // detection region
}
```

### `box` JSON Field Structure

```json
[0.7875, 0.3020833333333333, 0.159375, 0.43]  // [x, y, width, height] normalized 0-1
```

### `zones` JSON Field Structure

```json
[]  // Empty array = no zones configured; otherwise ["front_door", "yard"]
```

---

## 3. RECORDINGS Table

### Schema

```sql
CREATE TABLE "recordings" (
    "id" VARCHAR(30) NOT NULL PRIMARY KEY,
    "camera" VARCHAR(20) NOT NULL,          -- Camera name: "cam1"
    "path" VARCHAR(255) NOT NULL,           -- File path: /media/frigate/recordings/2026-07-18/14/cam1/53.31.mp4
    "start_time" DATETIME NOT NULL,         -- Unix timestamp (float)
    "end_time" DATETIME NOT NULL,           -- Unix timestamp (float)
    "duration" REAL NOT NULL,               -- Duration in seconds
    "objects" INTEGER,                      -- Number of detected objects in segment
    "motion" INTEGER,                       -- Number of motion regions detected
    "segment_size" REAL NOT NULL,           -- Segment file size in MB
    "dBFS" INTEGER,                         -- Audio level (decibels relative to full scale)
    "regions" INTEGER,                      -- Number of regions with activity
    "motion_heatmap" TEXT                   -- JSON heatmap: {"23": 26, "24": 26}
)
```

### Sample Data

| id | camera | path | start_time | duration | objects | motion |
|----|--------|------|------------|----------|---------|--------|
| `1784386411.0-vyrozp` | cam1 | `/media/frigate/recordings/2026-07-18/14/cam1/53.31.mp4` | 1784386411 (14:53:31) | 9.99s | 0 | 26 |
| `1784386401.0-u1l48y` | cam1 | `/media/frigate/recordings/2026-07-18/14/cam1/53.21.mp4` | 1784386401 (14:53:21) | 9.99s | 0 | 28 |

---

## 4. TIMELINE Table

### Schema

```sql
CREATE TABLE "timeline" (
    "timestamp" DATETIME NOT NULL,          -- Unix timestamp (float)
    "camera" VARCHAR(20) NOT NULL,          -- Camera name: "cam1"
    "source" VARCHAR(20) NOT NULL,          -- "tracked_object", "frigate", etc.
    "source_id" VARCHAR(30),                -- Related event ID
    "class_type" VARCHAR(50) NOT NULL,      -- "enter", "update", "gone", "active", "snapshot", "clip"
    "data" JSON                              -- Event data: box, label, score, etc.
)
```

### Sample Data

| timestamp | camera | source | source_id | class_type | data |
|------------|--------|--------|-----------|------------|------|
| 1784386206.97 (14:50:06) | cam1 | tracked_object | 1784386154.716448-7wjons | gone | `{"box":[...], "label":"person"}` |
| 1784386204.37 (14:50:04) | cam1 | tracked_object | 1784386154.716448-7wjons | active | `{"box":[...], "label":"person"}` |

### `class_type` Values

- `enter` — Object first detected
- `update` — Object position/score updated
- `active` — Object still being tracked
- `gone` — Object no longer visible
- `snapshot` — Snapshot taken
- `clip` — Video clip created

---

## 5. REVIEWSEGMENT Table

### Schema

```sql
CREATE TABLE "reviewsegment" (
    "id" VARCHAR(30) NOT NULL PRIMARY KEY,
    "camera" VARCHAR(20) NOT NULL,          -- Camera name: "cam1"
    "start_time" DATETIME NOT NULL,         -- Unix timestamp (float)
    "end_time" DATETIME,                    -- Unix timestamp (float), NULL while active
    "severity" VARCHAR(30) NOT NULL,        -- "alert", "detection", "motion"
    "thumb_path" VARCHAR(255) NOT NULL,     -- Thumbnail path
    "data" JSON NOT NULL                    -- Detection IDs and details
)
```

### Sample Data

| id | camera | start_time | end_time | severity | thumb_path |
|----|--------|------------|----------|----------|------------|
| `1784386072.168559-88d46o` | cam1 | 1784386072.17 (14:47:52) | 1784386206.97 (14:50:06) | alert | `/media/frigate/clips/review/thumb-cam1-...webp` |
| `1784381947.854754-5nmhnx` | cam1 | 1784381947.85 (13:39:07) | 1784381982.65 (13:39:42) | alert | `/media/frigate/clips/review/thumb-cam1-...webp` |

### `data` JSON Field Structure

```json
{
    "detections": ["1784386154.716448-7wjons", "1784386071.568256-yxsql4", ...],
    "severity": "alert",
    "type": "object"
}
```

---

## 6. OTHER TABLES

### USER Table

```sql
CREATE TABLE "user" (
    "username" VARCHAR(30) NOT NULL PRIMARY KEY,
    "password_hash" VARCHAR(120) NOT NULL,   -- pbkdf2_sha256 format
    "notification_tokens" JSON NOT NULL,     -- Push notification tokens
    "role" VARCHAR(20) NOT NULL DEFAULT 'admin',
    "password_changed_at" DATETIME
)
```

### REGIONS Table

```sql
CREATE TABLE "regions" (
    "camera" VARCHAR(20) NOT NULL PRIMARY KEY,
    "last_update" DATETIME NOT NULL,
    "grid" JSON                                -- Motion detection grid
)
```

### PREVIEWS Table

```sql
CREATE TABLE "previews" (
    "id" VARCHAR(30) NOT NULL PRIMARY KEY,
    "camera" VARCHAR(20) NOT NULL,
    "path" VARCHAR(255) NOT NULL,
    "start_time" DATETIME NOT NULL,
    "end_time" DATETIME NOT NULL,
    "duration" REAL NOT NULL
)
```

---

## 7. Key Relationships for Text-to-SQL

```
event.id  ←──→  timeline.source_id        (tracking lifecycle of detected object)
event.id  ←──→  reviewsegment.data.detections[]  (events grouped into review segments)
event.camera  ←──→  recordings.camera     (events from same camera)
event.start_time  ←──→  recordings.start_time  (events within recording time range)
```

---

## 8. Important Notes for LLM

1. **Time format**: All `start_time` and `end_time` fields are **Unix timestamps** (float, seconds since epoch). Convert with `datetime.fromtimestamp()` in Python or `datetime(timestamp, 'unixepoch')` in SQLite.

2. **ID format**: Event IDs follow pattern `{unix_timestamp}-{random_6chars}`, e.g. `1784386154.716448-7wjons`.

3. **Boolean fields**: `false_positive`, `has_clip`, `has_snapshot`, `retain_indefinitely` are `INTEGER` (0 or 1).

4. **JSON fields**: `zones`, `region`, `box`, `data` are JSON strings. Use `json_extract()` in SQLite to query nested values.

5. **Score field**: `score` and `top_score` may be `NULL` for some events (older events from Frigate 0.17).

6. **Detector info**: `detector_type` = `"onnx"`, `model_type` = `"yolo-generic"`, `model_hash` = MD5 of model file.

7. **Severity levels**: `reviewsegment.severity` can be `"alert"`, `"detection"`, or `"motion"`.

8. **Timeline class_type**: `"enter"`, `"update"`, `"active"`, `"gone"`, `"snapshot"`, `"clip"`.

---

## 9. Example SQL Queries for LLM

```sql
-- Get all person detections today
SELECT id, label, camera, start_time, end_time, score
FROM event
WHERE label = 'person' AND date(start_time, 'unixepoch') = date('now')
ORDER BY start_time DESC;

-- Count detections by label
SELECT label, COUNT(*) as count
FROM event
GROUP BY label
ORDER BY count DESC;

-- Get recordings with detected objects
SELECT id, camera, path, start_time, duration, objects, motion
FROM recordings
WHERE objects > 0
ORDER BY start_time DESC;

-- Get timeline for a specific event
SELECT timestamp, class_type, data
FROM timeline
WHERE source_id = '1784386154.716448-7wjons'
ORDER BY timestamp ASC;

-- Get review segments with their detections
SELECT id, camera, start_time, end_time, severity, data
FROM reviewsegment
ORDER BY start_time DESC;

-- Join events with recordings (events within recording time range)
SELECT e.id, e.label, e.start_time, r.path, r.duration
FROM event e
JOIN recordings r ON e.camera = r.camera
    AND e.start_time BETWEEN r.start_time AND r.end_time
ORDER BY e.start_time DESC;
```
