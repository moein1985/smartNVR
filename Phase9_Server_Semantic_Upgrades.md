# Phase 9: Server-Side Semantic Upgrades (Frigate + FastAPI)

**Status:** Planning — Approved  
**Date:** July 20, 2026  
**Target Server:** `192.168.85.203`  
**Prerequisites:** Phase 8 complete (production deployment running)

---

## Objective

Upgrade the Frigate NVR and FastAPI backend to support multi-class object detection, spatial zones, go2rtc live streaming, and recording segment retrieval — enabling both AI semantic queries ("How many cars entered parking 1 yesterday?") and the Flutter Classic NVR tab.

---

## Step 9.1: Configure go2rtc Live Streaming

**Goal:** Enable go2rtc restream so that WebRTC and MSE streaming endpoints become available for the Flutter app.

**File:** `/opt/frigate/config/config.yml` (on production server)

**Changes:**

Add a top-level `go2rtc` block with stream definitions for each camera and WebRTC candidate configuration:

```yaml
go2rtc:
  streams:
    cam1:
      - rtsp://admin:admin123@192.168.85.112:554/Streaming/Channels/101
      - "ffmpeg:cam1#audio=opus"
  webrtc:
    candidates:
      - 192.168.85.203:8555
```

**Notes:**
- The stream name (`cam1`) must match the camera name in the `cameras` block.
- The RTSP path uses the main stream (Channels/101) for highest quality live view.
- The `ffmpeg:cam1#audio=opus` line transcodes audio to Opus for WebRTC compatibility.
- Port 8555 (TCP+UDP) is already exposed in the Docker Compose file.
- After saving, restart Frigate: `docker restart frigate`

**Acceptance Criteria:**
- [ ] `go2rtc` block added to `config.yml` with `cam1` stream and WebRTC candidates
- [ ] Frigate restarted without entering Safe Mode
- [ ] `curl -s http://localhost:5000/api/go2rtc/streams` returns stream info
- [ ] RTSP restream accessible at `rtsp://192.168.85.203:8554/cam1`
- [ ] Frigate UI Live view shows camera stream (MSE or WebRTC)

---

## Step 9.2: Enable Multi-Class Object Detection

**Goal:** Expand detection beyond `person` to track `car`, `motorcycle`, `bicycle`, `dog`, and `cat`.

**File:** `/opt/frigate/config/config.yml` (on production server)

**Changes:**

Under `cameras.cam1.detect`, add an `objects` list:

```yaml
cameras:
  cam1:
    detect:
      enabled: true
      width: 640
      height: 480
      fps: 5
      objects:
        - person
        - car
        - motorcycle
        - bicycle
        - dog
        - cat
```

**Notes:**
- The YOLOv9-t-320 COCO model already detects all 80 classes. This config tells Frigate which labels to track and store as events.
- Additional classes will increase event table growth. Monitor DB size after deployment.
- After saving, restart Frigate: `docker restart frigate`

**Acceptance Criteria:**
- [ ] `objects` list added to `cameras.cam1.detect` with 6 labels
- [ ] Frigate restarted without errors
- [ ] After 10 minutes of operation, `SELECT DISTINCT label FROM event` returns more than just `person`
- [ ] Frigate UI shows detections for new labels

---

## Step 9.3: Define Zones via Frigate UI (Manual — User Task)

**Goal:** Create spatial zones (e.g., `parking_1`, `main_gate`) for zone-based filtering.

**This step is performed manually by the user via the Frigate web UI at `http://192.168.85.203:5000`.**

**Instructions for the user:**
1. Open Frigate UI in browser: `http://192.168.85.203:5000`
2. Navigate to **Settings → Cameras → cam1**
3. Scroll to the **Zones** section
4. Click **Add Zone** and draw a polygon on the camera image:
   - Zone 1: Name it `parking_1` — draw over the parking area
   - Zone 2: Name it `main_gate` — draw over the main entrance/gate
5. Click **Save** and restart Frigate when prompted

**Verification:**
- After restart, walk a person or drive a car through the defined zones
- Check: `sqlite3 /opt/frigate/config/frigate.db "SELECT zones FROM event WHERE zones != '[]' LIMIT 5"`
- Zones should appear as JSON arrays: `["parking_1"]`, `["main_gate"]`, or `["parking_1", "main_gate"]`

**Acceptance Criteria:**
- [ ] At least 2 zones defined (e.g., `parking_1`, `main_gate`) via Frigate UI
- [ ] Frigate config saved and restarted
- [ ] New events in the `event` table have non-empty `zones` JSON arrays
- [ ] Frigate UI shows zone overlays on the camera view

---

## Step 9.4: Update LLM Schema Context (frigate_schema.py)

**Goal:** Teach the LLM about zones, multi-class labels, and `json_each()` / `LIKE` filtering strategies.

**File:** `frigate-intelligence/src/frigate_intelligence/interface_adapters/schemas/frigate_schema.py`

**Changes:**

### 9.4.1: Update `SAMPLE_QUERIES`

Add zone-aware and multi-class sample queries:

```python
SAMPLE_QUERIES = """-- Get latest person detections
SELECT id, label, start_time, end_time, score FROM event WHERE label='person' ORDER BY start_time DESC LIMIT 10;

-- Count detections by label
SELECT label, COUNT(*) as count FROM event GROUP BY label;

-- Get recordings with objects
SELECT id, camera, path, start_time, duration, objects, motion FROM recordings WHERE objects > 0 ORDER BY start_time DESC;

-- Events in time range
SELECT * FROM event WHERE start_time BETWEEN 1784377610 AND 1784386200 ORDER BY start_time DESC;

-- Timeline for specific event
SELECT timestamp, class_type, data FROM timeline WHERE source_id='1784386154.716448-7wjons' ORDER BY timestamp ASC;

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
SELECT camera, label, zones, COUNT(*) as count, MAX(score) as max_score
FROM event
WHERE start_time > strftime('%s','now','-7 days')
GROUP BY camera, label, zones
ORDER BY count DESC;

-- Hourly detection count by label
SELECT label, strftime('%H', datetime(start_time, 'unixepoch', 'localtime')) as hour, COUNT(*) as count
FROM event
WHERE start_time > strftime('%s','now','-1 day')
GROUP BY label, hour
ORDER BY hour;"""
```

### 9.4.2: Update `SQL_RULES`

Add rules for zones and multi-class awareness:

```python
SQL_RULES = """1. Generate ONLY SELECT queries. No INSERT, UPDATE, DELETE, DROP, ALTER, or ATTACH.
2. Use SQLite syntax (json_extract for JSON fields).
3. Time fields are Unix timestamps (float). Use datetime(column, 'unixepoch', 'localtime') to convert.
4. Limit results to 100 rows maximum (add LIMIT 100).
5. Table names: event, recordings, timeline, reviewsegment, previews, regions, user.
6. Do not use markdown code fences in output. Return raw SQL only.
7. The `zones` column is a JSON array (e.g., ["parking_1"]). Use `LIKE '%zone_name%'` for simple filtering or `EXISTS (SELECT 1 FROM json_each(zones) WHERE value='zone_name')` for precise matching.
8. Available detection labels: person, car, motorcycle, bicycle, dog, cat.
9. Available zones: parking_1, main_gate (defined in Frigate config). If the user mentions a zone by description (e.g., "parking area"), map it to the closest zone name.
10. The `recordings` table has `path`, `start_time`, `end_time`, `duration` for 10-second MP4 segments stored at /media/frigate/recordings/YYYY-MM-DD/HH/<camera>/MM.SS.mp4."""
```

### 9.4.3: Add Dynamic Zone Injection (Optional Enhancement)

Add a function to fetch current zone names from Frigate API at startup:

```python
import urllib.request
import json

def get_frigate_zones(frigate_url: str = "http://localhost:5000") -> str:
    """Fetch zone names from Frigate API for LLM context."""
    try:
        config = json.loads(
            urllib.request.urlopen(f"{frigate_url}/api/config").read()
        )
        zones = []
        for cam_name, cam in config.get("cameras", {}).items():
            for zone_name in cam.get("zones", {}):
                zones.append(f"{zone_name} (camera: {cam_name})")
        if zones:
            return "Available zones: " + ", ".join(zones)
    except Exception:
        pass
    return "Available zones: parking_1, main_gate"
```

Integrate this into `PromptBuilder.build()` to dynamically include zone names in the system prompt.

**Acceptance Criteria:**
- [ ] `SAMPLE_QUERIES` includes at least 4 zone-related queries (LIKE, json_each, GROUP BY zones, hourly count)
- [ ] `SQL_RULES` includes rules 7–10 covering zones, labels, and recordings table
- [ ] Optional: `get_frigate_zones()` function fetches zone names from Frigate API
- [ ] `PromptBuilder.build()` includes zone context in system prompt
- [ ] LLM can generate correct SQL for "How many cars in parking_1 yesterday?"
- [ ] Backend restarted and tested with zone-based queries

---

## Step 9.5: Add `/api/v1/recordings` Endpoint (FastAPI)

**Goal:** Expose recording segment metadata via REST API for the Flutter playback tab.

**File:** `frigate-intelligence/src/frigate_intelligence/interface_adapters/controllers/api_controller.py`

**Changes:**

### 9.5.1: Add Pydantic Response Model

**File:** `frigate-intelligence/src/frigate_intelligence/interface_adapters/schemas/api_models.py`

```python
class RecordingSegment(BaseModel):
    id: str
    camera: str
    path: str
    start_time: float
    end_time: float
    duration: float
    objects: int | None = None
    motion: int | None = None


class RecordingListResponse(BaseModel):
    segments: list[RecordingSegment]
    total: int
    camera: str
    date: str | None = None
    hour: int | None = None
```

### 9.5.2: Add Repository Method

**File:** `frigate-intelligence/src/frigate_intelligence/infrastructure/database/frigate_sqlite_gateway.py`

```python
def get_recordings(
    self,
    camera: str | None = None,
    date: str | None = None,      # YYYY-MM-DD
    hour: int | None = None,      # 0-23
    start_time: float | None = None,
    end_time: float | None = None,
    limit: int = 500,
) -> list[dict]:
    """Query recordings table for VOD segments."""
    sql = "SELECT id, camera, path, start_time, end_time, duration, objects, motion FROM recordings"
    conditions = []
    params = []

    if camera:
        conditions.append("camera = ?")
        params.append(camera)
    if start_time:
        conditions.append("start_time >= ?")
        params.append(start_time)
    if end_time:
        conditions.append("end_time <= ?")
        params.append(end_time)
    if date:
        # Filter by date using unixepoch conversion
        conditions.append("date(start_time, 'unixepoch', 'localtime') = ?")
        params.append(date)
    if hour is not None:
        conditions.append("strftime('%H', datetime(start_time, 'unixepoch', 'localtime')) = ?")
        params.append(f"{hour:02d}")

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY start_time ASC LIMIT ?"
    params.append(limit)

    result = self.execute_sql(sql, tuple(params))
    if result.error:
        return []

    columns = result.columns
    return [dict(zip(columns, row)) for row in result.rows]
```

### 9.5.3: Add API Controller Method

**File:** `frigate-intelligence/src/frigate_intelligence/interface_adapters/controllers/api_controller.py`

```python
@router.get("/api/v1/recordings", response_model=RecordingListResponse)
async def get_recordings(
    camera: str | None = None,
    date: str | None = None,
    hour: int | None = None,
    start_time: float | None = None,
    end_time: float | None = None,
):
    """Retrieve recording segments for VOD playback."""
    segments = self._container.frigate_repo.get_recordings(
        camera=camera, date=date, hour=hour,
        start_time=start_time, end_time=end_time,
    )
    return RecordingListResponse(
        segments=[RecordingSegment(**s) for s in segments],
        total=len(segments),
        camera=camera or "all",
        date=date,
        hour=hour,
    )
```

### 9.5.4: Register Route

Ensure the new endpoint is registered in the FastAPI router (same pattern as existing `/api/v1/query` and `/api/v1/settings`).

**Acceptance Criteria:**
- [ ] `RecordingSegment` and `RecordingListResponse` Pydantic models defined
- [ ] `get_recordings()` method added to `FrigateSqliteGateway` with camera/date/hour/time-range filtering
- [ ] `GET /api/v1/recordings?camera=cam1&date=2026-07-20&hour=11` returns segment list
- [ ] `GET /api/v1/recordings?camera=cam1&start_time=1784547900&end_time=1784548100` returns segments in range
- [ ] Response includes `path` field usable as `http://<frigate_ip>:5000<path>` for VOD playback
- [ ] Endpoint tested via curl on production server

---

## Step 9.6: Add `/api/v1/cameras` Endpoint (FastAPI)

**Goal:** Expose camera and zone configuration to the Flutter app for dynamic UI rendering.

**File:** `frigate-intelligence/src/frigate_intelligence/interface_adapters/controllers/api_controller.py`

**Changes:**

Add a proxy endpoint that fetches camera config from Frigate and returns a simplified structure:

```python
@router.get("/api/v1/cameras")
async def get_cameras():
    """Return camera list with zones and detection labels."""
    # Fetch from Frigate API (internal HTTP call)
    import httpx
    frigate_url = "http://localhost:5000/api/config"
    async with httpx.AsyncClient() as client:
        resp = await client.get(frigate_url)
        config = resp.json()

    cameras = []
    for cam_name, cam in config.get("cameras", {}).items():
        cameras.append({
            "name": cam_name,
            "enabled": cam.get("enabled", False),
            "detect": {
                "width": cam.get("detect", {}).get("width", 0),
                "height": cam.get("detect", {}).get("height", 0),
                "fps": cam.get("detect", {}).get("fps", 0),
                "objects": cam.get("detect", {}).get("objects", ["person"]),
            },
            "zones": list(cam.get("zones", {}).keys()),
            "live_stream_name": cam.get("live", {}).get("stream_name", cam_name),
        })

    return {"cameras": cameras, "total": len(cameras)}
```

**Acceptance Criteria:**
- [ ] `GET /api/v1/cameras` returns camera list with names, zones, and detection labels
- [ ] Response includes zone names for each camera
- [ ] Response includes configured object labels for each camera
- [ ] Endpoint tested via curl on production server

---

## Step 9.7: Deploy and Verify

**Goal:** Rebuild and redeploy the backend container with all Phase 9 changes.

**Actions:**
1. Transfer updated source files to production server
2. Rebuild Docker image: `docker compose build frigate-intelligence`
3. Restart container: `docker compose up -d frigate-intelligence`
4. Verify all new endpoints:
   - `curl http://192.168.85.203:8088/api/v1/recordings?camera=cam1&date=2026-07-20`
   - `curl http://192.168.85.203:8088/api/v1/cameras`
   - `curl -X POST http://192.168.85.203:8088/api/v1/query -H 'Content-Type: application/json' -d '{"question":"how many cars in parking_1 yesterday"}'`
5. Verify Frigate streaming:
   - `curl http://192.168.85.203:5000/api/go2rtc/streams`
   - Open `http://192.168.85.203:5000` in browser → Live view should stream

**Acceptance Criteria:**
- [ ] Backend container rebuilt and running with new endpoints
- [ ] `/api/v1/recordings` returns recording segments
- [ ] `/api/v1/cameras` returns camera config with zones
- [ ] LLM correctly generates zone-filtered SQL queries
- [ ] Frigate Live view streams via go2rtc (MSE/WebRTC)
- [ ] Multi-class detections appearing in database
- [ ] No regressions in existing `/api/v1/query` and `/api/v1/settings` endpoints

---

## Summary Checklist

| Step | Description | Type | Status |
|------|-------------|------|--------|
| 9.1 | Configure go2rtc live streaming | Frigate config | [x] |
| 9.2 | Enable multi-class object detection | Frigate config | [x] |
| 9.3 | Define zones via Frigate UI | Manual (user) | [ ] |
| 9.4 | Update LLM schema context (zones, labels, sample queries) | Python code | [x] |
| 9.5 | Add `/api/v1/recordings` endpoint | Python code | [x] |
| 9.6 | Add `/api/v1/cameras` endpoint | Python code | [x] |
| 9.7 | Deploy and verify all changes | Deployment | [ ] |
