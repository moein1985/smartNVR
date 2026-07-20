# Technical Proposal: AI-First NVR Evolution

**Date:** July 20, 2026  
**Author:** Software Architect  
**Status:** Draft — Awaiting Approval

---

## Executive Summary

This proposal analyzes the feasibility of upgrading our current Frigate Intelligence Platform into a commercial "AI-First NVR" across two domains: (1) Server-side semantic upgrades and (2) Flutter mobile app evolution with a dual-tab architecture. The analysis is grounded in a live audit of the production server (`192.168.85.203`), Frigate's database schema, API surface, and streaming capabilities.

---

## Part 1: Feasibility Analysis

### 1.1 Expanding Object Detection (Multi-Class Tracking)

**Current state:** Frigate is configured with a YOLOv9-t-320 ONNX model (COCO 80-class). However, `config.yml` only tracks `person` (the default). The `event` table confirms: `SELECT DISTINCT label FROM event` returns only `person`.

**Feasibility: ✅ Straightforward**

The YOLOv9 COCO model already detects all 80 classes. Frigate filters which labels to track via the `objects` key in each camera's `detect` config. To enable multi-class tracking, we simply add:

```yaml
cameras:
  cam1:
    detect:
      enabled: true
      width: 640
      height: 480
      fps: 5
      # Add this block:
      objects:
        - person
        - car
        - motorcycle
        - bicycle
        - dog
        - cat
```

**Bottlenecks:**
- **GPU load:** Each additional tracked class slightly increases post-processing (NMS filtering, tracking). With a single camera at 5 FPS and a Tesla GPU, this is negligible. At scale (8+ cameras, 10+ FPS), we'd need to benchmark.
- **Database growth:** More labels → more events → larger SQLite DB. Current DB is 5.9 MB. With 6 labels, expect ~6× growth in the `event` table. SQLite handles this fine up to ~1 GB.
- **Labelmap:** The `coco-80.txt` labelmap is already mounted at `/config/labelmap/coco-80.txt`. No changes needed.

### 1.2 Zone Configuration

**Current state:** The `zones` field in the `event` table is a JSON array, currently always `[]` (empty). The Frigate config shows `"zones": {}` — no zones defined.

**Feasibility: ✅ Configured via Frigate UI (no code needed)**

Zones are defined in `config.yml` under each camera as polygon coordinates:

```yaml
cameras:
  cam1:
    zones:
      parking_1:
        coordinates: 0.1,0.1,0.5,0.1,0.5,0.5,0.1,0.5
      main_gate:
        coordinates: 0.6,0.3,0.9,0.3,0.9,0.8,0.6,0.8
```

Once zones are defined, Frigate automatically:
- Populates the `zones` JSON field in the `event` table (e.g., `["parking_1"]`)
- Supports zone-based filtering in its own UI

**Bottlenecks:**
- **Coordinate calibration:** Zone coordinates are normalized (0.0–1.0) relative to the detect resolution (640×480). We'll need to use Frigate's UI zone editor to draw polygons visually. This is a manual, one-time setup per camera.
- **Zone entry tracking:** Frigate distinguishes between "detected in zone" vs "entered zone". The `data` JSON field in `event` contains `path_data` with movement轨迹. For "how many cars *entered* parking 1", we need events where the zone appears in `zones` and the object was tracked entering (not just present).

### 1.3 AI Context Awareness (LLM + Zones + Labels)

**Current state:** Our `PromptBuilder` loads schema context from `Frigate_Database_Schema_Report.md` and provides sample queries. The LLM generates SQL against the `event` table.

**Feasibility: ✅ Requires schema context update + prompt engineering**

**What needs to change:**

1. **Update `frigate_schema.py`:** Add zone-aware sample queries and document the `zones` JSON field:
   ```sql
   -- Events in a specific zone
   SELECT id, label, camera, start_time FROM event 
   WHERE zones LIKE '%parking_1%' AND label='car' 
   ORDER BY start_time DESC LIMIT 100;
   ```

2. **SQL filtering on `zones`:** The `zones` column is JSON (e.g., `["parking_1", "main_gate"]`). SQLite's `LIKE` operator works for simple containment checks but is imprecise. For robust JSON querying, use `json_extract`:
   ```sql
   -- Exact zone match using JSON functions
   SELECT id, label, start_time FROM event
   WHERE EXISTS (
     SELECT 1 FROM json_each(event.zones) 
     WHERE value = 'parking_1'
   ) AND label = 'car';
   ```

3. **LLM prompt update:** The system prompt must explain that `zones` is a JSON array and teach the LLM to use `json_each()` for zone filtering. Add 2–3 zone-related sample queries to `SAMPLE_QUERIES`.

**Bottlenecks:**
- **LLM accuracy with `json_each()`:** Less common SQL pattern. The LLM might generate `LIKE '%parking_1%'` instead. This works as a fallback but can false-match (e.g., "parking_10" contains "parking_1"). We should include both patterns in sample queries and let the LLM pick.
- **No semantic zone metadata in DB:** The DB only stores zone *names* in the `zones` array. Zone geometry, friendly names, and descriptions live in `config.yml`. If the user asks "show me events near the main entrance", the LLM needs to know that "main entrance" = `main_gate` zone. We should inject the current zone definitions into the prompt context dynamically.

### 1.4 Frigate Streaming Capabilities (Critical Finding)

**Current state:** `go2rtc` config is **empty** (`{}`). No restream, MSE, or WebRTC is configured. Port 8555 is exposed in Docker but go2rtc has no streams defined.

**This is the single biggest blocker for the Classic NVR tab.**

**What needs to happen:**

1. **Configure go2rtc streams** in `config.yml`:
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

2. **Available streaming endpoints after configuration:**
   | Protocol | URL Pattern | Notes |
   |----------|------------|-------|
   | RTSP restream | `rtsp://192.168.85.203:8554/cam1` | Native RTSP, works with any player |
   | MSE (WebSocket) | `ws://192.168.85.203:5000/live/mse/api/ws?src=cam1` | Default for web, needs go2rtc |
   | WebRTC | `http://192.168.85.203:8555/` (SDP exchange) | Best for mobile, needs port 8555 TCP+UDP |
   | jsmpeg | `http://192.168.85.203:5000/api/jsmpeg/cam1` | Fallback, no go2rtc needed, low quality |

3. **Recording playback (VOD) — already working:**
   - Confirmed: `http://192.168.85.203:5000/recordings/2026-07-20/11/cam1/46.42.mp4` returns HTTP 200
   - Recordings are 10-second MP4 segments at `/recordings/YYYY-MM-DD/HH/<camera>/MM.SS.mp4`
   - The `recordings` table has `path`, `start_time`, `end_time`, `duration` for each segment

**Bottlenecks:**
- **go2rtc must be configured first** — without it, only jsmpeg (low quality, 10 FPS, 720p) is available for live streaming. This is the hard prerequisite for Domain 2.
- **WebRTC on mobile networks:** WebRTC requires port 8555 (TCP+UDP) to be accessible from the Flutter app's network. For LAN access, this works. For remote/internet access, we need port forwarding or a TURN server.
- **Recording segments are 10-second MP4s:** There's no single continuous MP4 for a given hour. Playback requires either (a) fetching the segment list from the `recordings` table and playing them sequentially, or (b) using Frigate's VOD endpoint which may stitch them. We confirmed individual segments are accessible via HTTP.

---

## Part 2: Flutter Architecture Recommendations

### 2.1 Dual-Tab Architecture

```
MainApp
├── Scaffold with BottomNavigationBar
│   ├── Tab 1: SmartAIPage (existing chat_page.dart, enhanced)
│   └── Tab 2: ClassicNVRPage (new)
│       ├── LiveViewTab (camera grid)
│       └── PlaybackTab (timeline + player)
```

**State management:** Continue with Riverpod. Add new providers:
- `liveStreamProvider` — manages active stream connections
- `recordingListProvider` — fetches recording segments from backend API
- `cameraConfigProvider` — fetches camera list and zone definitions from Frigate API

### 2.2 Live Streaming — Package Recommendations

| Strategy | Package | Pros | Cons | Recommendation |
|----------|---------|------|------|----------------|
| **WebRTC** | `flutter_webrtc` | Lowest latency (~200ms), native quality, audio support | Complex setup, needs port 8555 access, SDP exchange | ✅ **Primary** for LAN |
| **MSE** | Custom WebSocket + `media_kit` | Good quality, works through port 5000 | No standard Flutter MSE plugin, needs custom implementation | ⚠️ Fallback |
| **RTSP** | `media_kit` (with mpv backend) | Direct RTSP, no go2rtc needed | High latency (2-5s), battery drain, no mobile-optimized codec | ❌ Not recommended |
| **HLS** | `video_player` or `chewie` | Simple, HTTP-based | High latency (5-10s), needs go2rtc HLS output | ⚠️ Acceptable fallback |
| **jsmpeg** | Custom WebSocket + canvas | Works without go2rtc | Low quality (720p, 10fps), no audio, CPU-heavy | ❌ Last resort |

**Recommended approach:**

1. **Primary: WebRTC via `flutter_webrtc`**
   - Package: `flutter_webrtc: ^0.12.0`
   - Flow: Flutter app → POST SDP offer to `http://<frigate_ip>:8555/` → receive SDP answer → create RTCPeerConnection
   - Latency: ~200ms (excellent for live monitoring)
   - Requires: go2rtc configured + port 8555 accessible

2. **Fallback: HLS via `video_player`**
   - If WebRTC fails (NAT issues, port blocked), fall back to HLS
   - URL: `http://<frigate_ip>:5000/api/stream/cam1?mode=hls` (needs go2rtc)
   - Latency: 5-10s (acceptable for monitoring, not for PTZ control)

3. **Multi-camera grid:** Use `GridView.builder` with `AspectRatio` widgets. Each cell renders a `RTCVideoView` (WebRTC) or `VideoPlayer` (HLS). Limit to 4 simultaneous streams on mobile (GPU/memory constraints).

### 2.3 Recording Playback — Timeline Strategy

**Recommended approach:**

1. **Backend API extension:** Add a new endpoint to our FastAPI backend:
   ```
   GET /api/v1/recordings?camera=cam1&date=2026-07-20&hour=11
   → Returns: [{ "path": "/recordings/2026-07-20/11/cam1/46.42.mp4", "start_time": 1784548022, "end_time": 1784548032, "duration": 10 }, ...]
   ```
   This queries the `recordings` table and returns segment metadata.

2. **Flutter player:** Use `media_kit` (mpv-based) for VOD playback:
   - Package: `media_kit: ^1.2.0`, `media_kit_video: ^1.2.0`
   - URL: `http://<frigate_ip>:5000/recordings/2026-07-20/11/cam1/46.42.mp4`
   - `media_kit` handles HTTP MP4 playback natively, supports seeking, and is more robust than `video_player` for network streams.

3. **Timeline UI:** Custom `CustomPainter` widget drawing a 24-hour horizontal timeline:
   - Color-coded segments (motion = orange, continuous = blue, gaps = gray)
   - Tap on a segment → fetch segments for that hour → play first segment → auto-advance to next segment when current ends
   - Use `PageView` or a `ListView` of segment thumbnails (Frigate generates preview images)

4. **Seamless segment chaining:** When a segment finishes playing, automatically load the next segment from the list. Use a `PlaylistController` from `media_kit` or implement manual chaining with `onCompletion` callbacks.

### 2.4 Enhanced Smart AI Tab — Gallery & Clips

**Full-screen image gallery:**
- Wrap existing event gallery images in a `PageView` with `InteractiveViewer`
- Package: No extra package needed — `InteractiveViewer` is built into Flutter Material
- Pinch-to-zoom, swipe between events, double-tap to reset

**Inline video clip playback:**
- Frigate stores clips at `http://<frigate_ip>:5000/api/events/<event_id>/clip.mp4`
- Use `media_kit` or `chewie` + `video_player` for inline playback
- Check `has_clip == 1` in the event row before showing the play button
- Auto-play on tap, mute by default, tap to unmute

---

## Part 3: Database Querying Adaptations

### 3.1 Current Query Pattern

Our `TextToSQLUseCase` sends the user's question + schema context to the LLM, which generates a SQL query. The query runs against the `event` table in SQLite.

### 3.2 Filtering by `label` (Simple)

```sql
SELECT id, label, camera, start_time, end_time, score 
FROM event 
WHERE label = 'car' 
ORDER BY start_time DESC LIMIT 100;
```

No changes needed — `label` is a `VARCHAR(20)` column, direct equality works.

### 3.3 Filtering by `zones` (JSON Array — Needs Adaptation)

The `zones` column is JSON (e.g., `["parking_1"]`). Three approaches, in order of precision:

**Approach 1: `json_each()` (Most precise)**
```sql
SELECT id, label, camera, start_time 
FROM event 
WHERE label = 'car' 
  AND EXISTS (
    SELECT 1 FROM json_each(event.zones) 
    WHERE value = 'parking_1'
  )
ORDER BY start_time DESC;
```

**Approach 2: `LIKE` (Simpler, slight risk of false positives)**
```sql
SELECT id, label, camera, start_time 
FROM event 
WHERE label = 'car' 
  AND zones LIKE '%parking_1%'
ORDER BY start_time DESC;
```

**Approach 3: `json_extract` (For checking if zones is non-empty)**
```sql
SELECT id, label, zones FROM event 
WHERE json_array_length(zones) > 0;
```

**Recommendation:** Teach the LLM both Approach 1 and 2 via sample queries. Approach 1 is correct but the LLM may struggle with the subquery syntax. Approach 2 is a pragmatic fallback. Zone names are unlikely to be substrings of each other (e.g., "parking_1" vs "parking_10"), so `LIKE` is safe in practice.

### 3.4 Combined Label + Zone + Time Range

```sql
SELECT id, label, camera, 
       datetime(start_time, 'unixepoch', 'localtime') as start,
       datetime(end_time, 'unixepoch', 'localtime') as end_time,
       score
FROM event
WHERE label = 'car'
  AND EXISTS (SELECT 1 FROM json_each(zones) WHERE value = 'parking_1')
  AND start_time >= strftime('%s', '2026-07-19 00:00:00')
  AND start_time < strftime('%s', '2026-07-20 00:00:00')
ORDER BY start_time DESC;
```

### 3.5 Prompt Context Updates Needed

In `frigate_schema.py`, update:

1. **`SAMPLE_QUERIES`** — Add 3 zone-related examples:
   ```sql
   -- Count cars in parking_1 zone
   SELECT COUNT(*) FROM event WHERE label='car' AND zones LIKE '%parking_1%';
   
   -- Events by zone and label in last 24 hours
   SELECT label, zones, COUNT(*) as count FROM event 
   WHERE start_time > strftime('%s','now','-1 day') 
   GROUP BY label, zones;
   
   -- Zone entry events (objects that entered a zone)
   SELECT id, label, camera, start_time FROM event 
   WHERE EXISTS (SELECT 1 FROM json_each(zones) WHERE value='main_gate')
   ORDER BY start_time DESC LIMIT 50;
   ```

2. **`SQL_RULES`** — Add:
   - "The `zones` column is a JSON array (e.g., `["parking_1"]`). Use `LIKE '%zone_name%'` or `json_each()` for filtering."
   - "Available labels depend on detection config. Current labels: person, car, motorcycle, bicycle, dog, cat."
   - "Available zones: parking_1, main_gate (defined in Frigate config)."

3. **Dynamic zone injection:** Optionally, fetch zone names from Frigate's `/api/config` endpoint at startup and inject them into the prompt context. This ensures the LLM knows the exact zone names without hardcoding.

---

## Part 4: Risk Assessment & Prerequisites

### Critical Prerequisites (Must Do First)

| # | Prerequisite | Effort | Impact |
|---|-------------|--------|--------|
| 1 | Configure go2rtc streams in `config.yml` | Low (config change) | **Blocks all live streaming** |
| 2 | Add multi-class objects to detect config | Low (config change) | Blocks semantic queries for non-person labels |
| 3 | Define zones via Frigate UI | Low (manual UI work) | Blocks zone-based queries |
| 4 | Update LLM prompt context with zones + labels | Medium (code change) | Blocks AI context awareness |
| 5 | Add `/api/v1/recordings` endpoint to FastAPI | Medium (code change) | Blocks Flutter playback tab |

### Technical Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| WebRTC doesn't work over mobile network | Medium | Fallback to HLS; add TURN server later |
| LLM generates incorrect `json_each()` syntax | Medium | Include `LIKE` fallback in sample queries; retry logic already exists |
| SQLite performance degrades with multi-class growth | Low | Add index on `(label, start_time)`; migrate to PostgreSQL if >1M rows |
| go2rtc adds GPU/CPU overhead | Low | Monitor with `nvidia-smi`; go2rtc copies streams, doesn't decode |
| Flutter app memory pressure with multi-camera grid | Medium | Limit to 4 simultaneous streams; use `AutomaticDispose` providers |
| Recording segment chaining has gaps | Low | Frigate records continuously; segments are back-to-back with ~10s overlap |

---

## Part 5: Recommended Implementation Order

```
Phase 9: Semantic Upgrades (Server-Side)
  9.1  Configure go2rtc + multi-class detection + zones in Frigate
  9.2  Update LLM prompt context (schema, sample queries, zone injection)
  9.3  Add /api/v1/recordings endpoint to FastAPI backend
  9.4  Add /api/v1/cameras endpoint (proxy to Frigate /api/config for zone/camera info)

Phase 10: Flutter Dual-Tab Architecture
  10.1 Refactor to BottomNavigationBar with two tabs
  10.2 Enhance Smart AI Tab (full-screen gallery, inline clip playback)
  10.3 Implement Classic NVR Tab — Live View (WebRTC via flutter_webrtc)
  10.4 Implement Classic NVR Tab — Playback (timeline + media_kit VOD)
  10.5 Camera grid with multi-stream support
```

---

## Conclusion

The vision is **highly feasible** with no fundamental blockers. The single most critical prerequisite is configuring `go2rtc` in Frigate — without it, live streaming in the Flutter app is limited to low-quality jsmpeg. All other changes (multi-class detection, zones, LLM context, recording playback) are incremental additions to our existing architecture.

The recommended Flutter stack (`flutter_webrtc` for live + `media_kit` for VOD) is well-established and production-tested. The database querying adaptation is straightforward with `json_each()` or `LIKE` on the `zones` JSON column.

**Recommendation:** Proceed with Phase 9 (server-side) first, as it unblocks both the semantic AI features and the Flutter streaming prerequisites. Phase 10 (Flutter) can begin in parallel for the dual-tab scaffolding, with streaming features gated on go2rtc configuration.
