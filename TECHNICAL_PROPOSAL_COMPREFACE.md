# Technical Proposal: Facial Recognition Integration (Phase 11)

**Version:** 1.1  
**Date:** July 21, 2026  
**Author:** Software Architecture Team  
**Status:** Updated with GPU verification results  

---

## Executive Summary

This proposal analyzes the feasibility of integrating **CompreFace** (face recognition) and **DoubleTake** (middleware orchestrator) into our existing Frigate NVR system. The goal is a two-stage pipeline: Frigate detects `person`, DoubleTake intercepts the event, sends the snapshot to CompreFace, and writes the recognized name back to Frigate's `sub_label` field. Our FastAPI backend and Flutter app will then query `sub_label` to answer questions like "Was soleymani at his desk yesterday?"

**Verdict:** Feasible with constraints. **GPU verification completed:** The server has an **NVIDIA GeForce RTX 5050** (8 GB VRAM, Compute Capability **12.0**). CompreFace's GPU builds require CUDA 11.2 + MXNet, which supports a maximum CC of 8.6 — **the GPU build is incompatible with this GPU**. CompreFace must run in **CPU-only mode** (`exadel/compreface:1.1.0-arcface-r100` without `-gpu` suffix). This eliminates VRAM contention entirely but increases recognition latency to ~2–5s per image. MQTT must be enabled (currently disabled). DoubleTake handles the sub_label update automatically via Frigate's REST API — no custom integration code needed for the pipeline itself.

---

## 1. Docker & GPU Architecture

### 1.1 Current State

Our current `frigate-docker-compose.yml` runs a single Frigate container:

```yaml
frigate:
  image: ghcr.io/blakeblackshear/frigate:0.18.0-beta1-tensorrt
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            device_ids: ["0"]
            capabilities: ["gpu"]
  shm_size: "256m"
```

Frigate uses the GPU for YOLOv9-t-320 ONNX inference via TensorRT acceleration. Based on community benchmarks, this model consumes approximately **650–700 MB of VRAM** at 320×320 resolution, plus ~150 MB per ffmpeg stream for hardware decoding.

**Current estimated VRAM usage:** ~1.0–1.5 GB (model + 2 ffmpeg streams for cam1).

**Verified server GPU specs** (via `nvidia-smi` on `192.168.85.203`):

```
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.159.03             Driver Version: 580.159.03     CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
|   0  NVIDIA GeForce RTX 5050        Off |   00000000:01:00.0 Off |                  N/A |
|  0%   39C    P8              8W /  130W |       2MiB /   8151MiB |      0%      Default |
+-----------------------------------------+------------------------+----------------------+

name, compute_cap, memory.total [MiB], memory.free [MiB]
NVIDIA GeForce RTX 5050, 12.0, 8151 MiB, 7705 MiB
```

| Parameter | Value |
|-----------|-------|
| GPU Model | NVIDIA GeForce RTX 5050 |
| Compute Capability | **12.0** |
| Total VRAM | 8,151 MiB (~8 GB) |
| Free VRAM | 7,705 MiB (~7.5 GB) |
| CUDA Version (Driver) | 13.0 |
| Driver Version | 580.159.03 |

> **Note:** At time of inspection, Frigate showed only 2 MiB VRAM usage — it had just restarted (Up 3 minutes). VRAM usage will increase to ~1.0–1.5 GB once detection is actively processing camera feeds.

### 1.2 CompreFace GPU Requirements

CompreFace offers multiple model variants with different VRAM footprints:

| Model | VRAM (idle) | VRAM (under load) | Accuracy | Recommended GPU |
|-------|-------------|--------------------|----------|-----------------|
| `arcface-r100-gpu` | ~1.5 GB | ~2.7–3.0 GB | Highest | 6 GB+ |
| `arcface-r50-gpu` | ~1.2 GB | ~2.0–2.5 GB | High | 4 GB+ |
| `arcface_mobilefacenet-gpu` | ~720 MB | ~1.0–1.2 GB | Medium | 4 GB |
| `arcface-r100-gpu` (CPU mode) | 0 MB GPU | 0 MB GPU | Highest | Any (slow) |

**Critical finding (VERIFIED):** CompreFace uses **MXNet with CUDA 11.2**, which supports GPUs with Compute Capability 3.5–8.6. Our server's RTX 5050 has **CC 12.0** — far exceeding the supported range. **All CompreFace GPU builds are incompatible with this GPU.** The MXNet library is effectively unmaintained, and CompreFace developers have acknowledged this limitation with no timeline for a fix.

| CompreFace Image | CC Required | RTX 5050 (CC 12.0) | Status |
|------------------|-------------|---------------------|--------|
| `arcface-r100-gpu` | ≤ 8.6 | CC 12.0 | ❌ Incompatible |
| `arcface_mobilefacenet-gpu` | ≤ 8.6 | CC 12.0 | ❌ Incompatible |
| `arcface-r100` (CPU-only) | N/A | N/A | ✅ **Only option** |

**Recommendation:** Use **CPU-only CompreFace** (`exadel/compreface:1.1.0-arcface-r100` without `-gpu` suffix). The 8 GB VRAM is sufficient, but the CC 12.0 incompatibility is a hard blocker for GPU acceleration.

### 1.3 GPU Sharing Feasibility

> **Updated finding:** Since CompreFace must run in CPU-only mode (CC 12.0 incompatibility), **GPU sharing is no longer a concern**. Frigate has exclusive access to the full 8 GB VRAM. CompreFace will use system RAM and CPU cores instead.

For reference, if GPU sharing were possible, the VRAM budget would be:

| Component | Idle VRAM | Peak VRAM |
|-----------|-----------|-----------|
| Frigate (YOLOv9-t + 2 ffmpeg) | ~1.0 GB | ~1.5 GB |
| CompreFace (arcface_mobilefacenet-gpu) | ~0.7 GB | ~1.2 GB |
| CompreFace (arcface-r100-gpu) | ~1.5 GB | ~3.0 GB |
| **Total (MobileNet)** | **~1.7 GB** | **~2.7 GB** |
| **Total (ArcFace-R100)** | **~2.5 GB** | **~4.5 GB** |

**If the server has 4 GB VRAM:** Use `arcface_mobilefacenet-gpu` only. ArcFace-R100 will OOM.
**If the server has 6 GB VRAM:** ArcFace-R100 is feasible with `uwsgi_processes=1`.
**If the server has 8 GB+ VRAM:** ArcFace-R100 with `uwsgi_processes=1` is comfortable.

> **Actual situation:** These thresholds are **moot** for our deployment. The RTX 5050 (CC 12.0) cannot run any CompreFace GPU build. CompreFace runs on CPU, using system RAM instead of VRAM. Frigate retains exclusive GPU access.

**No CUDA context conflicts exist** — Frigate uses ONNX Runtime/TensorRT on GPU, CompreFace uses MXNet on CPU. They do not compete for GPU resources at all.

### 1.4 Proposed Docker Compose Architecture

```yaml
# docker-compose.yml (unified, on server 192.168.85.203)

services:
  # --- Existing ---
  frigate:
    container_name: frigate
    image: ghcr.io/blakeblackshear/frigate:0.18.0-beta1-tensorrt
    restart: unless-stopped
    shm_size: "256m"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["0"]
              capabilities: ["gpu"]
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /opt/frigate/config:/config
      - /mnt/record50/frigate:/media/frigate
      - type: tmpfs
        target: /tmp/cache
        tmpfs:
          size: 1000000000
    privileged: true
    ports:
      - "5000:5000"
      - "8554:8554"
      - "8555:8555/tcp"
      - "8555:8555/udp"
    environment:
      FRIGATE_RTSP_PASSWORD: "frigate_rtsp_pass"
    depends_on:
      - mosquitto

  # --- New: MQTT Broker ---
  mosquitto:
    container_name: mosquitto
    image: eclipse-mosquitto:2
    restart: unless-stopped
    ports:
      - "1883:1883"
    volumes:
      - /opt/mosquitto/config:/mosquitto/config
      - /opt/mosquitto/data:/mosquitto/data
      - /opt/mosquitto/log:/mosquitto/log

  # --- New: CompreFace (CPU-only — RTX 5050 CC 12.0 incompatible with GPU builds) ---
  compreface-core:
    container_name: compreface-core
    image: exadel/compreface:1.1.0-arcface-r100  # CPU-only, NO -gpu suffix
    restart: unless-stopped
    # No GPU deploy section — CompreFace runs on CPU
    ports:
      - "8000:80"
    volumes:
      - compreface-db:/var/lib/postgresql/data
    environment:
      - POSTGRES_URL=jdbc:postgresql://compreface-db:5432/frigate
      - SPRING_PROFILES_ACTIVE=api
      - API_IMG_LENGTH_LIMIT=640
      - CONNECTOR_TIMEOUT=10000
      - ML_PORT=3000
      - UWSGI_PROCESSES=2   # CPU mode can handle 2 processes
      - UWSGI_THREADS=1
    depends_on:
      - compreface-db

  compreface-db:
    container_name: compreface-db
    image: exadel/compreface-postgres:1.1.0
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=frigate

  # --- New: DoubleTake ---
  double-take:
    container_name: double-take
    image: jakowenko/double-take:latest
    restart: unless-stopped
    ports:
      - "3001:3000"
    volumes:
      - /opt/double-take:/double-take/data
    depends_on:
      - mosquitto
      - compreface-core

volumes:
  compreface-db:
```

### 1.5 Network Considerations

All containers should be on the same Docker network. DoubleTake needs to reach:
- Mosquitto at `mosquitto:1883` (MQTT)
- Frigate at `frigate:5000` (REST API for snapshots and sub_label updates)
- CompreFace at `compreface-core:80` (face recognition API)

Our existing `frigate-intelligence` container already uses the `frigate_default` network. The new containers should join the same network.

### 1.6 Potential Bottleneck: CPU Recognition Latency

**Risk Level: Medium** — CompreFace runs in CPU-only mode (RTX 5050 CC 12.0 is incompatible with CompreFace's CUDA 11.2 / MXNet GPU builds). CPU inference with ArcFace-R100 takes **~2–5 seconds per image**, compared to ~0.3s on GPU.

**Impact on pipeline:** DoubleTake retries up to 10 times per event (configurable). With `stop_on_match: true`, it stops on the first successful match. For a 5 FPS detection camera, there are multiple snapshot opportunities within the event window. The first good-quality face frame typically yields a match.

**Mitigation:**
- Use `stop_on_match: true` to short-circuit on first match
- Set `attempts.latest: 10` and `attempts.snapshot: 10` for more retry opportunities
- Configure Frigate MQTT snapshot `crop: true` and `height: 500` for tighter, higher-quality face images
- Consider `arcface_mobilefacenet` CPU build for faster inference (~1–2s) if accuracy is sufficient
- Monitor CPU usage on the server — if CPU is bottlenecked, reduce `UWSGI_PROCESSES` to 1

---

## 2. Data Flow & Frigate API

### 2.1 Current MQTT State

Our `frigate-config.yml` has **MQTT disabled**:

```yaml
mqtt:
  enabled: false
```

**This is a hard blocker.** DoubleTake relies entirely on MQTT to receive Frigate events. We must enable MQTT and add a Mosquitto broker container.

### 2.2 Required Frigate Config Changes

```yaml
mqtt:
  enabled: true
  host: mosquitto    # Docker service name
  port: 1883
  topic_prefix: frigate
  client_id: frigate
  # stats_interval: 60

cameras:
  cam1:
    # ... existing config ...
    mqtt:
      enabled: true
      crop: true          # Crop to bounding box — improves face recognition
      quality: 90         # Higher quality for better recognition
      height: 500         # Larger image for DoubleTake
```

The `mqtt.crop: true` setting is important — it crops the snapshot to the detected object's bounding box, giving CompreFace a tighter face image instead of the full frame.

### 2.3 DoubleTake Configuration

DoubleTake's `config.yml`:

```yaml
mqtt:
  host: mosquitto
  port: 1883
  topics:
    frigate: frigate/events
    matches: double-take/matches
    cameras: double-take/cameras

frigate:
  url: http://frigate:5000
  update_sub_labels: true       # Key: writes sub_label back to Frigate
  stop_on_match: true           # Stop retrying once a match is found
  labels:
    - person
  attempts:
    latest: 10                  # Try latest.jpg up to 10 times
    snapshot: 10                # Try snapshot.jpg up to 10 times
    mqtt: true                  # Also process MQTT snapshot topics
    delay: 0                    # No delay between attempts

detectors:
  compreface:
    url: http://compreface-core:80
    key: <compreface_api_key>   # Obtained after creating CompreFace app
    timeout: 15
    det_prob_threshold: 0.5     # Minimum confidence for face detection
    opencv_face_required: false # Don't require OpenCV pre-check
```

### 2.4 Data Flow Sequence

```
1. Camera → Frigate
   Frigate detects "person" via YOLOv9 ONNX/TensorRT

2. Frigate → Mosquitto (MQTT)
   Publishes to frigate/events:
   {
     "before": { "id": "1784386154.716448-7wjons", "label": "person", "camera": "cam1", ... },
     "after":  { "id": "1784386154.716448-7wjons", "label": "person", "camera": "cam1", ... },
     "type": "new"
   }

3. DoubleTake ← Mosquitto (MQTT subscription)
   DoubleTake receives frigate/events message
   Extracts: event_id, camera, label="person"

4. DoubleTake → Frigate (HTTP GET)
   GET http://frigate:5000/api/events/{event_id}/snapshot.jpg
   GET http://frigate:5000/api/cam1/latest.jpg?h=500
   (retries up to 10 times for each, with delay=0)

5. DoubleTake → CompreFace (HTTP POST)
   POST http://compreface-core:80/api/v1/recognition/recognize
   Body: multipart/form-data with image file
   Header: x-api-key: <compreface_api_key>

6. CompreFace → DoubleTake (HTTP Response)
   {
     "result": [
       {
         "subjects": [
           { "subject": "soleymani", "similarity": 0.78 }
         ]
       }
     ]
   }

7. DoubleTake → Frigate (HTTP POST — sub_label update)
   POST http://frigate:5000/api/events/{event_id}/sub_label
   Body: { "subLabel": "soleymani", "subLabelScore": 0.78 }
   
   Or if no match:
   Body: { "subLabel": "unknown", "subLabelScore": null }

8. DoubleTake → Mosquitto (MQTT publish)
   Publishes to double-take/matches/soleymani:
   {
     "id": "1784386154.716448-7wjons",
     "camera": "cam1",
     "match": { "name": "soleymani", "confidence": 78.0, "detector": "compreface" }
   }
```

### 2.5 How DoubleTake Updates Frigate's sub_label

DoubleTake uses Frigate's REST API endpoint:

```
POST /api/events/{event_id}/sub_label
Content-Type: application/json

{ "subLabel": "soleymani", "subLabelScore": 0.78 }
```

This endpoint was added in Frigate 0.11.0 (PR #2949). Our server runs **0.18.0-beta1**, which includes this endpoint. The endpoint requires `admin` role authentication, but our Frigate instance currently has no authentication enabled (no login required), so DoubleTake can call it directly.

**Important timing issue:** Community reports indicate that if DoubleTake is slow (e.g., CompreFace takes 5+ seconds), the sub_label may be set **after** the Frigate review item has already been finalized. In this case, the sub_label is written to the SQLite database but may not appear in the Frigate UI's review timeline. However, **the database record is updated regardless**, which is what our FastAPI backend queries.

### 2.6 SQLite Database Impact

The `sub_label` column in the `event` table is `VARCHAR(100)` and nullable. DoubleTake writes:
- The recognized subject name (e.g., `"soleymani"`)
- `"unknown"` if no match found
- `NULL` if face detection found no face

Multiple subjects can be comma-separated: `"soleymani, ahmad"` if two faces are recognized in the same frame.

**No schema migration is needed.** The column already exists and is populated by Frigate's internal event metadata updater when the REST API is called.

---

## 3. Backend & LLM Adaptation

### 3.1 Current Schema Context for LLM

Our `frigate_schema.py` provides the LLM with database schema context. Currently, the `sub_label` column is mentioned in the schema report but **not in the SQL rules or sample queries**. The LLM has no explicit guidance on when or how to use `sub_label`.

Current `SQL_RULES` (line 94–108 of `frigate_schema.py`) include rules about labels, zones, timestamps, and score extraction — but nothing about `sub_label` or person identification.

### 3.2 Required Changes to `frigate_schema.py`

#### 3.2.1 Add Sample Queries

Add to `SAMPLE_QUERIES`:

```python
SAMPLE_QUERIES = """-- ... existing queries ...

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
ORDER BY start_time DESC LIMIT 50;
"""
```

#### 3.2.2 Add SQL Rules

Add to `SQL_RULES`:

```python
SQL_RULES = """... existing rules ...

16. CRITICAL: The `sub_label` column contains the recognized person's name when facial recognition is active. Values can be a single name (e.g., 'soleymani'), comma-separated names for multiple faces (e.g., 'soleymani, ahmad'), 'unknown' for unrecognized faces, or NULL if no facial recognition was performed.
17. When the user asks about a specific person by name (e.g., "Was soleymani at his desk?"), you MUST filter on `sub_label='person_name'` in addition to `label='person'`. Do NOT search by the `label` column alone — `label` only contains the object class ('person'), not the identity.
18. When the user asks "who was seen" or "who came today", query `SELECT DISTINCT sub_label FROM event WHERE label='person' AND sub_label IS NOT NULL`.
19. When the user asks about "unknown" or "unrecognized" people, filter on `sub_label='unknown'`.
20. The `sub_label` may contain comma-separated values for multiple faces. Use `LIKE '%person_name%'` for flexible matching, or exact match `sub_label='person_name'` for single-face events."""
```

#### 3.2.3 Update Fallback Schema String

Update the fallback schema in `load_schema_context()`:

```python
return """Frigate SQLite Database Schema:
Tables: event, recordings, timeline, reviewsegment, previews, regions, user
Key table: event (id VARCHAR, label VARCHAR, camera VARCHAR, start_time DATETIME, end_time DATETIME, score REAL, sub_label VARCHAR, zones JSON, data JSON)
Time format: Unix timestamps (float, seconds since epoch)
Camera: cam1
Labels: person, car, motorcycle, bicycle, dog, cat
Sub-labels: recognized person names (e.g., 'soleymani'), 'unknown', or NULL
Zones: configured via Frigate UI (e.g., parking_1, main_gate)"""
```

### 3.3 LLM Prompt Impact

The LLM (currently GPT-4o via LangChain) will need to learn the concept of `sub_label` as a person identity field. The key challenge is **disambiguation**:

| User Question | LLM Should Generate |
|---------------|---------------------|
| "How many people were seen today?" | `SELECT COUNT(*) FROM event WHERE label='person' AND start_time >= strftime('%s','now','start of day')` |
| "Was soleymani seen today?" | `SELECT id, datetime(start_time,'unixepoch','localtime') FROM event WHERE label='person' AND sub_label='soleymani' AND start_time >= strftime('%s','now','start of day')` |
| "Who came to the office yesterday?" | `SELECT DISTINCT sub_label, datetime(start_time,'unixepoch','localtime') FROM event WHERE label='person' AND sub_label IS NOT NULL AND start_time BETWEEN ...` |
| "Show me unknown faces" | `SELECT id, camera, datetime(start_time,'unixepoch','localtime') FROM event WHERE label='person' AND sub_label='unknown'` |

The distinction between "people" (generic `label='person'`) and "specific person" (`sub_label='name'`) must be explicit in the rules. Without rule #17, the LLM will likely generate `WHERE label='soleymani'` which returns zero results because `label` only contains `'person'`.

### 3.4 No Code Changes to Use Case Logic

The `TextToSQLUseCase` class and `SQLValidator` need **no changes**. The LLM generates SQL that includes `sub_label` filters naturally once the schema context and rules are updated. The `SQLValidator` already allows any SELECT query on the `event` table.

The `FrigateSqliteGateway._row_to_event()` method already maps `sub_label` at index 15 (line 137 of `frigate_sqlite_gateway.py`). The `Event` entity already has the `sub_label` field (line 21 of `event.py`).

### 3.5 Flutter App Impact

The Flutter app's event gallery (`chat_bubble.dart`) displays event snapshots. When `sub_label` is populated, we should show the recognized name as a badge or overlay on the snapshot. This is a UI enhancement, not a breaking change.

The `EventItem` model in `api_models.py` does not currently include `sub_label`. We should add it:

```python
class EventItem(BaseModel):
    id: str
    label: str
    sub_label: str | None = None  # NEW
    camera: str
    start_time: float
    end_time: float | None
    score: float | None
    has_clip: int
    has_snapshot: int
    zones: list[str]
    detector_type: str | None
    model_type: str | None
```

---

## 4. Potential Bottlenecks & Risks

### 4.1 CPU Recognition Latency (Medium Risk — Confirmed)

**Issue:** CompreFace must run in CPU-only mode due to RTX 5050's Compute Capability 12.0 being incompatible with CompreFace's CUDA 11.2 / MXNet dependency. CPU inference with ArcFace-R100 takes ~2–5 seconds per image.

**Mitigation:**
- Use `stop_on_match: true` to short-circuit on first match
- Set `attempts.latest: 10` and `attempts.snapshot: 10` for more retry opportunities
- Configure Frigate MQTT snapshot `crop: true` and `height: 500` for tighter face images
- Consider `arcface_mobilefacenet` CPU build for faster inference (~1–2s) if accuracy is sufficient
- Monitor server CPU usage — reduce `UWSGI_PROCESSES` to 1 if CPU is bottlenecked
- **No VRAM contention** — Frigate has exclusive GPU access, CompreFace uses system RAM

### 4.2 CompreFace CUDA Compatibility (Confirmed — Resolved)

**Issue:** CompreFace uses CUDA 11.2 and MXNet. GPUs with Compute Capability > 8.6 are not supported by the GPU build. MXNet is effectively unmaintained.

**Verified finding:** Server GPU is **RTX 5050 with CC 12.0** — far exceeds the maximum supported CC of 8.6. All CompreFace GPU builds are incompatible.

**Resolution:**
- **Use CPU-only CompreFace image:** `exadel/compreface:1.1.0-arcface-r100` (no `-gpu` suffix)
- This is a **hard constraint**, not a configurable option
- Monitor CompreFace GitHub for PyTorch migration (planned, no timeline)
- If GPU acceleration becomes critical in the future, consider alternatives like `insightface` (PyTorch-based, supports modern CUDA)

### 4.3 MQTT Latency & Timing (Medium Risk — Amplified by CPU Mode)

**Issue:** DoubleTake must process the MQTT event, fetch the snapshot, send to CompreFace, and update the sub_label — all before the Frigate review item is finalized. With CPU-only CompreFace (~2–5s per recognition attempt), the total pipeline time per attempt is ~3–6s (including HTTP overhead). If this takes > 10 seconds, the sub_label may not appear in the Frigate UI review timeline (though it will be in the database).

**Mitigation:**
- Use `stop_on_match: true` to short-circuit on first match
- Set `det_prob_threshold: 0.5` to avoid processing low-confidence faces
- Use `mqtt.crop: true` in Frigate config for tighter face images
- Increase `attempts.latest` and `attempts.snapshot` to 10 for more retry opportunities
- **Database record is always updated** regardless of UI timing — our FastAPI backend reads from SQLite, not the UI

### 4.4 Recognition Accuracy (Low Risk)

**Issue:** The camera at `192.168.85.112` (cam1) is a Hikvision channel 102 (sub-stream, 640×480). Face images may be too small for reliable recognition.

**Mitigation:**
- Use channel 101 (main stream, higher resolution) for snapshot extraction — but this is the recording stream, not the detection stream
- Configure Frigate's MQTT snapshot `height: 500` to upscale
- Use ArcFace-R100 CPU (highest accuracy model — CPU mode does not reduce accuracy, only speed)
- Train CompreFace with multiple angles per subject (minimum 5 photos recommended)

### 4.5 Database Concurrency (Low Risk)

**Issue:** Both Frigate (writing events) and our FastAPI backend (reading events) access the SQLite database. DoubleTake's REST API call triggers Frigate to UPDATE the `event` table. SQLite handles concurrent reads well, but writes are serialized.

**Mitigation:** SQLite WAL mode (enabled by default in Frigate 0.18+) allows concurrent reads during writes. No action needed.

### 4.6 DoubleTake Project Status (Medium Risk)

**Issue:** The original DoubleTake repository (`jakowenko/double-take`) is no longer actively maintained. Community forks exist but may lag behind Frigate API changes.

**Mitigation:**
- Use the latest published Docker image (`jakowenko/double-take:latest`)
- The core functionality (MQTT subscription, Frigate API calls, CompreFace integration) is stable
- If issues arise, DoubleTake's logic is simple enough to reimplement as a Python service in our `frigate-intelligence` backend

---

## 5. Implementation Prerequisites

Before writing any roadmap or code:

1. ~~**Verify server GPU model and VRAM**~~ — ✅ **COMPLETED**: RTX 5050, 8 GB VRAM, CC 12.0
2. ~~**Check CUDA Compute Capability**~~ — ✅ **COMPLETED**: CC 12.0 > 8.6 max — CompreFace GPU builds incompatible. **Decision: CPU-only mode.**
3. **Enable MQTT in Frigate config** — Change `mqtt.enabled: false` to `true` and add Mosquitto container
4. **Test CompreFace standalone** — Deploy CompreFace CPU-only, create an application, obtain API key, register a test subject
5. **Test DoubleTake standalone** — Configure DoubleTake, verify it can subscribe to MQTT and call Frigate API
6. **Verify sub_label endpoint** — `curl -X POST http://192.168.85.203:5000/api/events/{event_id}/sub_label -H "Content-Type: application/json" -d '{"subLabel":"test"}'`
7. **Monitor CPU usage** — After deploying CompreFace CPU-only, verify server CPU can handle the inference load alongside Frigate and frigate-intelligence

---

## 6. Architecture Diagram

```
                    ┌─────────────┐
                    │   Camera    │
                    │ 192.168.85  │
                    │   .112      │
                    └──────┬──────┘
                           │ RTSP
                           ▼
┌──────────────────────────────────────────────┐
│              Frigate Container               │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐  │
│  │  ffmpeg  │→│ YOLOv9-t  │→│  Event DB  │  │
│  │ (decode) │  │ (ONNX/    │  │ (SQLite)   │  │
│  │          │  │  TensorRT)│  │            │  │
│  └─────────┘  └──────────┘  └──────┬─────┘  │
│       │                          │         │
│       │ MQTT: frigate/events     │ REST    │
│       ▼                          │ API     │
└───────┬──────────────────────────┼─────────┘
        │                          │
        ▼                          │
┌──────────────┐                   │
│  Mosquitto   │                   │
│  (MQTT       │                   │
│   Broker)    │                   │
└──────┬───────┘                   │
       │                           │
       ▼                           │
┌──────────────────────┐           │
│    DoubleTake        │───────────┘
│  ┌───────────────┐   │ GET /api/events/{id}/snapshot.jpg
│  │ MQTT Subscribe│   │ POST /api/events/{id}/sub_label
│  └───────┬───────┘   │
│          │           │
│  ┌───────▼───────┐   │
│  │ Face Rec      │   │
│  │ Orchestrator  │   │
│  └───────┬───────┘   │
│          │           │
└──────────┼───────────┘
           │ POST /api/v1/recognition/recognize
           ▼
┌──────────────────────┐
│   CompreFace (CPU)   │
│  ┌────────────────┐  │
│  │ ArcFace-R100   │  │
│  │ (MXNet/CPU     │  │
│  │  mode — GPU    │  │
│  │  incompatible  │  │
│  │  with RTX 5050 │  │
│  │  CC 12.0)      │  │
│  └────────────────┘  │
│  ┌────────────────┐  │
│  │ PostgreSQL DB  │  │
│  │ (face vectors) │  │
│  └────────────────┘  │
└──────────────────────┘

                    ┌──────────────────────┐
                    │ frigate-intelligence │
                    │   (FastAPI backend)  │
                    │                      │
                    │  Reads event table   │
                    │  including sub_label │
                    │  via SQLite gateway  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Flutter NVR App    │
                    │  (Riverpod + AI)     │
                    │                      │
                    │  "Was soleymani at   │
                    │   his desk yesterday?"│
                    │  → LLM generates SQL  │
                    │  → WHERE sub_label=  │
                    │    'soleymani'       │
                    └──────────────────────┘
```

---

## 7. Summary & Recommendations

| Area | Feasibility | Key Constraint |
|------|-------------|----------------|
| Docker & GPU sharing | ✅ Feasible (CPU-only) | RTX 5050 CC 12.0 incompatible with CompreFace GPU builds — CompreFace runs on CPU. No VRAM contention. |
| MQTT pipeline | ✅ Feasible | Must enable MQTT (currently disabled) and add Mosquitto container |
| DoubleTake → Frigate sub_label | ✅ Feasible | Uses existing REST API `POST /api/events/{id}/sub_label`; no custom code needed |
| Backend LLM adaptation | ✅ Feasible | Update `frigate_schema.py` with sub_label rules and sample queries; no code logic changes |
| Flutter app | ✅ Feasible | Add `sub_label` to `EventItem` model; optional UI badge for recognized names |
| Recognition accuracy | ⚠️ Depends | Camera resolution (640×480 sub-stream) may limit accuracy; ArcFace-R100 CPU provides highest accuracy |
| CPU latency | ⚠️ Medium risk | ~2–5s per recognition on CPU; mitigated by `stop_on_match: true` and 10 retries |

### Recommended Next Steps

1. ~~SSH to `192.168.85.203` and run `nvidia-smi`~~ — ✅ **Done**: RTX 5050, 8 GB VRAM, CC 12.0
2. ~~Choose CompreFace image tag~~ — ✅ **Decided**: `exadel/compreface:1.1.0-arcface-r100` (CPU-only)
3. **Enable MQTT in Frigate config** and add Mosquitto container
4. **Deploy CompreFace CPU-only** and register test subjects
5. **Deploy DoubleTake** and verify end-to-end pipeline
6. **Monitor CPU usage** on server during recognition load
7. **Update `frigate_schema.py`** with sub_label rules
8. **Write Phase 11 roadmap** with detailed implementation steps
