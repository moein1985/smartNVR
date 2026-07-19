# Phase 8: Production Deployment on the Main Frigate Server (192.168.85.203)

**Status:** Planning — Awaiting Green Light  
**Date:** July 19, 2026  
**Target Server:** `192.168.85.203` (live Frigate NVR)  
**Previous Server:** `192.168.85.202` (staging, to be decommissioned)

---

## 1. Server Analysis Results (192.168.85.203)

### 1.1 Running Containers

| Container | Image | Status | Ports |
|-----------|-------|--------|-------|
| `frigate` | `ghcr.io/blakeblackshear/frigate:0.18.0-beta1-tensorrt` | Up 20h (healthy) | `5000→5000`, `8554-8555→8554-8555` |

- **Port 8088:** ✅ Available (no conflicts)
- **Port 3000:** ✅ Available (no conflicts)
- **Port 5000:** ❌ Occupied by Frigate (expected — this is the Frigate Web UI / API)

### 1.2 Frigate Database

| Property | Value |
|----------|-------|
| Absolute path | `/opt/frigate/config/frigate.db` |
| Size | 5.9 MB |
| Owner | `root:root` |
| Permissions | `0644` (`-rw-r--r--`) |
| WAL files | `frigate.db-wal` (4.0 MB), `frigate.db-shm` (32 KB) — **active** |
| Last modified | 2026-07-19 10:14 (live, actively written by Frigate) |

**Config directory:** `/opt/frigate/config/` contains `config.yml`, `frigate.db`, `backup.db`, `model_cache/`, `labelmap/`, and other Frigate runtime files.

### 1.3 Docker Networks

| Network | Driver | Scope | Used By |
|---------|--------|-------|---------|
| `bridge` | bridge | local | (default) |
| `frigate_default` | bridge | local | `frigate` container |
| `host` | host | local | — |
| `none` | null | local | — |

Frigate container is on `frigate_default` network (gateway `172.18.0.1`, IP `172.18.0.2`).

### 1.4 Frigate Volume Mounts

```yaml
volumes:
  - /etc/localtime:/etc/localtime:ro
  - /opt/frigate/config:/config:rw
  - /mnt/record50/frigate:/media/frigate:rw
  - type: tmpfs
    target: /tmp/cache
    tmpfs:
      size: 1000000000
```

The DB is accessible inside the Frigate container at `/config/frigate.db`.

### 1.5 System Resources

| Resource | Value |
|----------|-------|
| Disk (root `/`) | 73G total, 63G used, **6.5G available** (91% — ⚠️ low) |
| Memory | 30 GiB total, 3.9 GiB used, ~26 GiB available |
| Swap | 8 GiB (59 MiB used) |
| Docker Compose | v2.40.3 |

### 1.6 Frigate docker-compose.yml Location

`/opt/frigate/docker-compose.yml`

---

## 2. Architecture & Deployment Plan

### 2.1 Architecture Overview

```
192.168.85.203 (Production Server)
├── frigate container (existing, untouched)
│   ├── Port 5000 (Frigate UI/API)
│   ├── Volume: /opt/frigate/config → /config
│   └── Network: frigate_default
│
├── frigate-intelligence container (NEW — Backend)
│   ├── Port 8088 → 8000
│   ├── Volume: /opt/frigate/config → /opt/frigate/config:ro  (read-only, live DB)
│   ├── Network: frigate_default (join existing Frigate network)
│   └── Env: FRIGATE_DB_PATH=/opt/frigate/config/frigate.db
│
└── frigate-web-panel container (NEW — Frontend)
    ├── Port 3000 → 3000
    ├── Network: frigate_default
    └── Env:
        ├── NEXT_PUBLIC_API_URL=http://192.168.85.203:8088
        └── NEXT_PUBLIC_FRIGATE_URL=http://192.168.85.203:5000
```

### 2.2 Key Architecture Decisions

1. **Read-Only DB Mount (`:ro`):** The backend will mount `/opt/frigate/config` as **read-only** (`/opt/frigate/config:/opt/frigate/config:ro`). This is critical because:
   - Frigate is actively writing to `frigate.db-wal` and `frigate.db-shm`
   - SQLite supports concurrent read access from multiple processes
   - Read-only mount prevents our backend from accidentally corrupting the live DB
   - **Note:** SQLite WAL mode allows multiple readers + 1 writer. Our backend only executes `SELECT` queries, so this is safe.

2. **Join `frigate_default` Network:** Both new containers will join the existing `frigate_default` Docker network. This enables:
   - Internal DNS resolution (`frigate` hostname reachable from backend)
   - Low-latency container-to-container communication
   - No need for host network exposure for internal calls

3. **Environment Variable Updates:**
   - `NEXT_PUBLIC_API_URL` → `http://192.168.85.203:8088`
   - `NEXT_PUBLIC_FRIGATE_URL` → `http://192.168.85.203:5000`
   - `FRIGATE_DB_PATH` → `/opt/frigate/config/frigate.db` (same path inside container)

4. **Disk Space Warning:** Only 6.5 GB free on root partition. Docker images + build cache may consume 2-3 GB. Monitor closely. Consider pruning old images with `docker image prune -f` before deployment.

---

## 3. Migration Steps

### Step 8.1: Prepare .203 Server

```bash
# Create deployment directory
sudo mkdir -p /opt/frigate-intelligence
sudo chown moein:moein /opt/frigate-intelligence

# Prune old Docker images to free disk space
docker image prune -f
docker builder prune -f
```

### Step 8.2: Transfer Project Code to .203

From local machine:
```powershell
# Create tarball (excluding node_modules, .next, .venv, etc.)
tar -cf deploy_phase8.tar --exclude=.venv --exclude=__pycache__ --exclude=node_modules --exclude=.next --exclude=openapi.json --exclude=generated.ts frigate-intelligence frigate-web-panel

# Upload to .203
pscp -batch -pw 1234321 deploy_phase8.tar moein@192.168.85.203:/tmp/deploy_phase8.tar
```

On .203:
```bash
# Extract
cd /opt/frigate-intelligence
tar -xf /tmp/deploy_phase8.tar
```

### Step 8.3: Update docker-compose.yml for Production

The `docker-compose.yml` on `.203` must be updated with:

```yaml
services:
  frigate-intelligence:
    build: ./frigate-intelligence
    container_name: frigate-intelligence
    restart: unless-stopped
    ports:
      - "8088:8000"
    volumes:
      # Read-only mount to live Frigate DB
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

**Key changes from Phase 7:**
- Volume mount changed to `:ro` (read-only — live DB safety)
- Network changed from `frigate-net` (internal) to `frigate_default` (external, shared with Frigate)
- `NEXT_PUBLIC_API_URL` updated from `.202` to `.203`
- `NEXT_PUBLIC_FRIGATE_URL` updated from `.203:5000` (same, but now same host)
- Build context paths adjusted for nested directory structure

### Step 8.4: Update .env for Production

Create `/opt/frigate-intelligence/frigate-intelligence/.env` on `.203`:

```env
FRIGATE_DB_PATH=/opt/frigate/config/frigate.db
AVALAI_API_KEY=<existing_key>
AVALAI_BASE_URL=<existing_base_url>
LLM_MODEL=<existing_model>
MAX_SQL_RETRIES=3
```

### Step 8.5: Stop Old Instances on .202

```bash
# On 192.168.85.202
cd /opt/frigate-intelligence
docker compose down
```

### Step 8.6: Build & Start on .203

```bash
# Start backend first (needed for frontend API type generation)
cd /opt/frigate-intelligence
docker compose up --build -d frigate-intelligence

# Wait for backend health
sleep 10
curl http://localhost:8088/api/v1/health

# Build and start frontend
docker compose up --build -d frigate-web-panel
```

### Step 8.7: Verify Production Stack

```bash
# Check containers
docker ps --filter name=frigate

# Backend health
curl http://192.168.85.203:8088/api/v1/health

# Frontend
curl -o /dev/null -w "%{http_code}" http://192.168.85.203:3000

# Analytics endpoint
curl http://192.168.85.203:8088/api/v1/analytics/summary

# Test query
curl -X POST http://192.168.85.203:8088/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "last 5 events", "max_retries": 1}'
```

### Step 8.8: Cleanup .202 (Optional)

```bash
# Remove old containers and images on .202
docker compose down --rmi all
```

---

## 4. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Disk space (6.5 GB free) | ⚠️ Medium | Prune Docker cache before build; monitor with `df -h` |
| Read-only mount breaks SQLite | 🟢 Low | SQLite WAL mode supports read-only connections; backend only runs SELECTs |
| Frigate DB locked by Frigate | 🟢 Low | SQLite allows concurrent readers; Frigate is the sole writer |
| Port conflict | 🟢 None | Ports 8088 and 3000 confirmed free |
| Network isolation | 🟢 Low | Joining `frigate_default` as external network is standard Docker practice |
| Frigate container restart | 🟢 None | Our containers are independent; Frigate restart won't affect them |

---

## 5. Acceptance Criteria

- [ ] `frigate-intelligence` container running on `.203:8088` with `db_connected: true`
- [ ] `frigate-web-panel` container running on `.203:3000` returning HTTP 200
- [ ] Chat queries return results from the live `frigate.db`
- [ ] Snapshot thumbnails load from `192.168.85.203:5000/api/events/{id}/snapshot.jpg`
- [ ] Analytics dashboard renders charts with live data
- [ ] Streaming responses work (SSE typing effect)
- [ ] Old containers on `.202` stopped
- [ ] No disruption to the running Frigate instance on `.203`

---

## 6. Rollback Plan

If deployment fails or causes issues on `.203`:
1. `docker compose down` on `.203` (stops our containers, Frigate untouched)
2. Restart containers on `.202` as fallback
3. Investigate logs: `docker logs frigate-intelligence`, `docker logs frigate-web-panel`
