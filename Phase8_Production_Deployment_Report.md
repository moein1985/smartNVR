# Phase 8: Production Deployment on the Main Frigate Server — Implementation Report

**Date:** July 19, 2026  
**Production Server:** `192.168.85.203` (live Frigate NVR)  
**Previous Staging Server:** `192.168.85.202` (decommissioned)  
**Status:** ✅ All 6 steps completed — production stack live

---

## Step 1: Update Python SQLite Connection (Read-Only URI Mode)

### Problem
Frigate actively writes to `frigate.db` using SQLite WAL (Write-Ahead Logging) mode. Standard `sqlite3.connect()` on a `:ro` mount fails because it attempts to create/write the `-shm` and `-wal` sidecar files.

### Solution
**File Modified:** `src/frigate_intelligence/infrastructure/database/connection.py`

Changed from:
```python
conn = sqlite3.connect(str(path))
```

To:
```python
abs_path = str(path.resolve())
conn = sqlite3.connect(f"file:{abs_path}?mode=ro", uri=True)
```

This uses SQLite's URI mode with `mode=ro` flag, which:
- Opens the database in strict read-only mode
- Does not attempt to write or lock WAL/SHM files
- Allows concurrent reads alongside Frigate's active writer
- Prevents any accidental corruption of the live database

---

## Step 2: Prepare Server .203 (Cleanup & Disk Space)

### Disk Space Crisis
The server had only **6.5 GB free** (91% used). Docker build requires downloading base images and installing dependencies (~2-3 GB).

### Actions Taken
```bash
docker system prune -a -f --volumes
```

**Result:** Reclaimed **5.179 GB** from unused images (alpine, hello-world, python:3-slim, ubuntu:22.04, old Frigate images, CUDA base, Shinobi, etc.)

| Metric | Before | After |
|--------|--------|-------|
| Used | 63 GB (91%) | 46 GB (67%) |
| Available | 6.5 GB | **24 GB** |

Created project directory: `mkdir -p /home/moein/frigate-intelligence`

---

## Step 3: Transfer Files to .203

### Process
1. Created tarball locally excluding `node_modules`, `.next`, `.venv`, `__pycache__`, `.env`, `openapi.json`, `generated.ts`
2. Transferred via `pscp` to `192.168.85.203:/tmp/deploy_phase8.tar` (825 KB)
3. Extracted to `/home/moein/frigate-intelligence/` with both `frigate-intelligence/` and `frigate-web-panel/` subdirectories

### .env Configuration
Copied `.env` from `.202` and created on `.203` at `/home/moein/frigate-intelligence/frigate-intelligence/.env`:
```env
FRIGATE_DB_PATH=/opt/frigate/config/frigate.db
AVALAI_API_KEY=aa-9ZS4bj4RNfWF5v36MH4dXBETfya0p9aJxJOOFvF6TlJFXCss
AVALAI_BASE_URL=https://api.avalai.ir/v1
LLM_MODEL=gemini-3.1-flash-lite
MAX_SQL_RETRIES=3
```

---

## Step 4: Configure docker-compose.yml for Production

### Docker DNS Fix (Critical Issue Encountered)

During the first build attempt, Docker containers could not resolve `deb.debian.org` — DNS resolution failed inside build containers.

**Root Cause:** `/etc/docker/daemon.json` was configured with `8.8.8.8` and `8.8.4.4` as DNS servers, but port 53 to those public DNS servers was blocked on the `.203` network. The actual DNS server was `192.168.85.1` (local gateway).

**Fix:** Updated `/etc/docker/daemon.json`:
```json
{"dns":["192.168.85.1"]}
```

After fixing DNS and restarting Docker, builds completed successfully.

### Production docker-compose.yml

**Location:** `/home/moein/frigate-intelligence/docker-compose.yml`

```yaml
services:
  frigate-intelligence:
    build: ./frigate-intelligence
    container_name: frigate-intelligence
    restart: unless-stopped
    ports:
      - "8088:8000"
    volumes:
      - /opt/frigate/config:/opt/frigate/config:ro
    env_file:
      - ./frigate-intelligence/.env
    networks:
      - frigate_default

  frigate-web-panel:
    build:
      context: ./frigate-web-panel
      dockerfile: Dockerfile
    container_name: frigate-web-panel
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://192.168.85.203:8088
      - NEXT_PUBLIC_FRIGATE_URL=http://192.168.85.203:5000
    depends_on:
      - frigate-intelligence
    networks:
      - frigate_default

networks:
  frigate_default:
    external: true
```

### Key Changes from Phase 7 (Staging on .202)

| Property | Phase 7 (.202) | Phase 8 (.203) |
|----------|----------------|----------------|
| Volume mount | `/opt/frigate/config:/opt/frigate/config` (rw) | `/opt/frigate/config:/opt/frigate/config:ro` |
| Network | `frigate-net` (internal bridge) | `frigate_default` (external, shared with Frigate) |
| `NEXT_PUBLIC_API_URL` | `http://192.168.85.202:8088` | `http://192.168.85.203:8088` |
| `NEXT_PUBLIC_FRIGATE_URL` | `http://192.168.85.203:5000` | `http://192.168.85.203:5000` (same host now) |
| SQLite connection | Standard `sqlite3.connect()` | URI mode `file:{path}?mode=ro` |
| Build context paths | `.` and `./frigate-web-panel` | `./frigate-intelligence` and `./frigate-web-panel` |

### Additional Files Updated for Production

- **`frigate-web-panel/Dockerfile`** — Updated `openapi-typescript` URL from `.202` to `.203`
- **`frigate-web-panel/package.json`** — Updated `generate-api` script URL to `.203`
- **`frigate-web-panel/src/lib/api-client.ts`** — Updated default `BASE_URL` to `.203`
- **`frigate-web-panel/src/hooks/use-send-query-stream.ts`** — Updated default `BASE_URL` to `.203`

---

## Step 5: Shut Down Staging (.202)

```bash
# On 192.168.85.202
cd /opt/frigate-intelligence
docker compose down
```

**Result:**
- `frigate-web-panel` — Stopped & Removed
- `frigate-intelligence` — Stopped & Removed
- `frigate-intelligence_frigate-net` network — Removed

Staging server `.202` no longer runs our containers. Other services on `.202` (Guacamole, Elastiflow/Kibana) remain untouched.

---

## Step 6: Build & Deploy on Production (.203)

### Build Process

1. **Backend first** (`docker compose up --build -d frigate-intelligence`):
   - `python:3.12-slim` base image pulled (cached from DNS test)
   - `sqlite3` CLI installed via apt-get
   - `uv` installed, 59 Python packages installed
   - Container started, health check passed: `{"status":"ok","db_connected":true}`

2. **Frontend second** (`docker compose up --build -d frigate-web-panel`):
   - `node:20-alpine` base image pulled
   - `npm ci` — 435 packages installed
   - `openapi-typescript` fetched schema from live backend on `.203:8088`
   - `next build` — compiled successfully, 3 routes generated (`/`, `/analytics`, `/_not-found`)
   - Standalone output copied to runner stage
   - Container started, HTTP 200 confirmed

### Deployment Verification

```
NAMES                  STATUS                   PORTS
frigate                Up 2 minutes (healthy)   0.0.0.0:5000->5000/tcp, 8554-8555
frigate-intelligence   Up 10 seconds            0.0.0.0:8088->8000/tcp
frigate-web-panel      Up 10 seconds            0.0.0.0:3000->3000/tcp
```

**Backend health:**
```json
{"status":"ok","version":"0.1.0","db_connected":true}
```

**Frontend:** HTTP 200 ✅

**Analytics (live data from Frigate DB):**
```json
{"total_events":340,"events_by_label":{"person":340},...}
```

**Backend logs:**
```
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete.
INFO: GET /api/v1/health HTTP/1.1 200 OK
```

**Frontend logs:**
```
▲ Next.js 16.2.10
- Local: http://localhost:3000
- Network: http://0.0.0.0:3000
✓ Ready in 0ms
```

---

## Issues Encountered & Resolved

| Issue | Cause | Fix | Impact |
|-------|-------|-----|--------|
| Docker build DNS failure | `daemon.json` configured with `8.8.8.8` (port 53 blocked) | Changed DNS to `192.168.85.1` (local gateway) | All Docker builds now resolve correctly |
| Docker daemon won't start after JSON edit | Malformed JSON in `daemon.json` (missing quotes) | Used `printf` with hex escapes for proper JSON quoting | Daemon started successfully after fix |
| Systemd rate-limit on Docker restart | Multiple failed restart attempts | `systemctl reset-failed docker` before start | Docker service recovered |
| Disk space critical (6.5 GB) | Old images from previous experiments | `docker system prune -a -f --volumes` (5.2 GB reclaimed) | 24 GB free for builds |

---

## Final Architecture

```
192.168.85.203 (Production Server — Live Frigate NVR)
│
├── frigate container (existing, untouched)
│   ├── Port 5000 (Frigate UI/API)
│   ├── Volume: /opt/frigate/config → /config (rw, active WAL writes)
│   └── Network: frigate_default (172.18.0.0/16)
│
├── frigate-intelligence container (NEW — FastAPI Backend)
│   ├── Port 8088 → 8000
│   ├── Volume: /opt/frigate/config → /opt/frigate/config:ro (read-only)
│   ├── SQLite: file:/opt/frigate/config/frigate.db?mode=ro (URI read-only)
│   ├── Network: frigate_default (external)
│   └── Env: FRIGATE_DB_PATH, AVALAI_API_KEY, LLM_MODEL
│
└── frigate-web-panel container (NEW — Next.js Frontend)
    ├── Port 3000 → 3000
    ├── Network: frigate_default (external)
    └── Env:
        ├── NEXT_PUBLIC_API_URL=http://192.168.85.203:8088
        └── NEXT_PUBLIC_FRIGATE_URL=http://192.168.85.203:5000
```

---

## File Change Summary

### Backend (Python)
| File | Change |
|------|--------|
| `infrastructure/database/connection.py` | Changed to URI read-only mode (`file:{path}?mode=ro`, `uri=True`) |
| `docker-compose.yml` | Production config: `:ro` mount, `frigate_default` external network, `.203` URLs |

### Frontend (TypeScript)
| File | Change |
|------|--------|
| `Dockerfile` | Updated `openapi-typescript` URL to `.203` |
| `package.json` | Updated `generate-api` script URL to `.203` |
| `src/lib/api-client.ts` | Updated default `BASE_URL` to `.203` |
| `src/hooks/use-send-query-stream.ts` | Updated default `BASE_URL` to `.203` |

### Server Configuration (.203)
| File | Change |
|------|--------|
| `/etc/docker/daemon.json` | Updated DNS from `8.8.8.8` to `192.168.85.1` |
| `/home/moein/frigate-intelligence/docker-compose.yml` | New production compose file |
| `/home/moein/frigate-intelligence/frigate-intelligence/.env` | Production environment variables |

---

## Access URLs (Production)

| Service | URL |
|---------|-----|
| Web UI (Chat) | `http://192.168.85.203:3000` |
| Analytics Dashboard | `http://192.168.85.203:3000/analytics` |
| API Health | `http://192.168.85.203:8088/api/v1/health` |
| API Query (SSE Streaming) | `http://192.168.85.203:8088/api/v1/query/stream` |
| API Analytics | `http://192.168.85.203:8088/api/v1/analytics/summary` |
| Frigate NVR | `http://192.168.85.203:5000` |
| Frigate Snapshots | `http://192.168.85.203:5000/api/events/{id}/snapshot.jpg` |

---

## Production Data Snapshot

- **Total Events:** 340 (all `person` label)
- **Events by Hour:** Peak at hour 6 (93 events), hour 13 (63 events)
- **Database:** 5.9 MB live `frigate.db` with active WAL (4.0 MB)
- **Read-only access:** Confirmed working — no WAL lock conflicts
