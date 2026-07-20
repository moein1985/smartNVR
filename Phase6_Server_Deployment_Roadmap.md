# Phase 6: Server Deployment (Docker) — Detailed Roadmap

**Status:** ✅ Completed  
**Date Completed:** July 2026

## Architectural Pivots (Phase 6)
- Initially deployed to staging server `192.168.85.202`, later migrated to production server `192.168.85.203` (Phase 8).
- Backend container exposes port 8000, mapped to host port 8088 to avoid conflicts.
- Frigate DB mounted read-only (`/opt/frigate/config:/opt/frigate/config:ro`).

---

## Objective

Deploy the Frigate Intelligence Platform as a Docker container on an Ubuntu server, ensuring the REST API is accessible, the Avalai LLM is connected, and the Frigate database is mounted for querying.

---

## Prerequisites

- Phases 1–3 and 5 complete (Domain, Use Cases, Infrastructure, API, Bots, Analytics, POS)
- Ubuntu server with SSH access
- Docker and Docker Compose installed on the server
- Frigate NVR running (either on the same server or accessible via network mount)
- Avalai API key obtained
- Project source code ready at `frigate-intelligence/`

---

## Step 6.1: Dockerfile

**File: `frigate-intelligence/Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY src/ ./src/

RUN uv pip install --system --no-cache .

EXPOSE 8000

CMD ["python", "-m", "frigate_intelligence.server"]
```

**Key decisions:**
- **Base image**: `python:3.12-slim` — minimal footprint, Python 3.12+ required for `X | None` syntax
- **sqlite3 installed** — needed for `FrigateSqliteGateway` to read the Frigate DB
- **uv pip install --system** — installs package into system Python (no venv inside container)
- **CMD uses `server.py`** — not `frigate-ai serve`, because the FastAPI app factory requires a DI `Container` argument that must be constructed at runtime

**Acceptance Criteria:**
- [x] Dockerfile builds without errors
- [x] Image size is reasonable (<500MB)
- [x] `sqlite3` is available inside the container
- [x] Application starts with `python -m frigate_intelligence.server`

---

## Step 6.2: Server Entrypoint

**File: `src/frigate_intelligence/server.py`**

```python
import uvicorn

from frigate_intelligence.config.settings import Settings
from frigate_intelligence.config.dependencies import create_container
from frigate_intelligence.infrastructure.api.fastapi_app import create_app


def main():
    settings = Settings()
    container = create_container(settings)
    app = create_app(container)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
```

**Why this file exists:**
The `create_app(container)` factory in `fastapi_app.py` requires a `Container` object. The CLI `frigate-ai serve` command also works, but for Docker the `server.py` module is cleaner — it avoids Typer argument parsing overhead and directly boots uvicorn with the correct DI wiring.

**Acceptance Criteria:**
- [x] `server.py` creates `Settings`, `Container`, and `FastAPI` app in correct order
- [x] Uvicorn binds to `0.0.0.0:8000` (accessible outside container)
- [x] `python -m frigate_intelligence.server` starts the API without errors

---

## Step 6.3: Docker Compose Configuration

**File: `frigate-intelligence/docker-compose.yml`**

```yaml
version: "3.8"

services:
  frigate-intelligence:
    build: .
    container_name: frigate-intelligence
    restart: unless-stopped
    ports:
      - "8088:8000"
    volumes:
      - /opt/frigate/config:/opt/frigate/config:ro
    env_file:
      - .env
    networks:
      - frigate-net

networks:
  frigate-net:
    driver: bridge
```

**Key decisions:**
- **Port `8088:8000`** — port 8080 was already in use by an existing container (`flow-collector`). Use `8088` externally, map to `8000` internally.
- **Volume mount `/opt/frigate/config`** — mounts the Frigate config directory read-only so the container can access `frigate.db`. If Frigate runs on a different server, use NFS/SMB mount or copy the DB file.
- **`restart: unless-stopped`** — container auto-restarts on crash or server reboot, but stays stopped if manually stopped.
- **Custom bridge network `frigate-net`** — isolates container networking; can be shared with Frigate container if on same host.
- **`env_file: .env`** — injects all environment variables (API keys, DB path, model name) without hardcoding in compose.

**Acceptance Criteria:**
- [x] `docker compose up -d` starts the container
- [x] Port 8088 is mapped and accessible externally
- [x] Frigate DB path is mounted read-only
- [x] Container restarts automatically on failure
- [x] Environment variables are loaded from `.env`

---

## Step 6.4: .dockerignore

**File: `frigate-intelligence/.dockerignore`**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
build/
.env
.git/
tests/
Archive_Pre_Deployment/
```

**Why:**
- `.env` excluded — secrets should not be baked into the image; injected via `env_file` in compose
- `tests/` excluded — not needed in production image
- `.venv/`, `__pycache__/`, `.git/` — build artifacts and VCS data, reduce image size

**Acceptance Criteria:**
- [x] `.env` is NOT in the Docker image
- [x] Test files are NOT in the Docker image
- [x] Build context is minimal (faster builds)

---

## Step 6.5: .env Configuration

**File: `frigate-intelligence/.env` (on server)**

```env
FRIGATE_DB_PATH=/opt/frigate/config/frigate.db
AVALAI_API_KEY=aa-9ZS4bj4RNfWF5v36MH4dXBETfya0p9aJxJOOFvF6TlJFXCss
AVALAI_BASE_URL=https://api.avalai.ir/v1
LLM_MODEL=gemini-3.1-flash-lite
MAX_SQL_RETRIES=3

# Telegram Bot (optional, for Phase 3 bot runner)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Bale Bot (optional, for Phase 3 bot runner)
BALE_BOT_TOKEN=
BALE_CHAT_ID=

# POS API (optional, for Phase 5 POS correlation)
POS_API_URL=
POS_API_KEY=
```

**Important notes:**
- `AVALAI_BASE_URL` must be `https://api.avalai.ir/v1` (NOT `https://avalai.ir/v1`)
- `FRIGATE_DB_PATH` inside the container must match the mount path in `docker-compose.yml`
- If Frigate DB is at a different location on the host, update both the volume mount and this path

**Acceptance Criteria:**
- [x] `.env` file exists on server with real API key
- [x] `AVALAI_BASE_URL` is correct (`https://api.avalai.ir/v1`)
- [x] `FRIGATE_DB_PATH` matches the volume mount path
- [x] `.env` is in `.gitignore` and `.dockerignore`

---

## Step 6.6: Transfer Project to Server

**Method: SCP / PSCP (Windows)**

```powershell
# From Windows machine to Ubuntu server
# Using pscp (PuTTY SCP) on Windows:
pscp -r C:\Users\Moein\Documents\Codes\YOLO\frigate-intelligence moein@192.168.85.202:/home/moein/frigate-intelligence

# Or using scp (if OpenSSH client installed):
scp -r C:\Users\Moein\Documents\Codes\YOLO\frigate-intelligence moein@192.168.85.202:/home/moein/frigate-intelligence
```

**Post-transfer checklist:**
```bash
# SSH into server
ssh moein@192.168.85.202

# Verify files transferred
cd /home/moein/frigate-intelligence
ls -la
# Should see: Dockerfile, docker-compose.yml, pyproject.toml, src/, .env, .env.example

# Verify .env has real values
cat .env
```

**Acceptance Criteria:**
- [x] Project files transferred to `/home/moein/frigate-intelligence/` on server
- [x] `Dockerfile`, `docker-compose.yml`, `pyproject.toml`, `src/` directory present
- [x] `.env` file present with real API key (not placeholder)

---

## Step 6.7: Check Existing Containers

Before deploying, check what's already running on the server to avoid port conflicts:

```bash
# List all running containers
docker ps

# Check which ports are in use
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
```

**Known containers on 192.168.85.202:**

| Container | Port | Status |
|-----------|------|--------|
| guacamole-guacamole-1 | 8081 | Running |
| guacamole-db-1 | 3306 | Running |
| guacamole-guacd-1 | 4822 | Running |
| elastiflow-kibana | 5601 | Running |
| flow-collector | 8080 | Running |
| elastiflow-elasticsearch | 9200 | Running |

**Port conflict resolution:**
- Port `8080` was occupied by `flow-collector` → changed to `8088`
- If `8088` is also taken, use `8089`, `8090`, etc.

**Acceptance Criteria:**
- [x] Existing containers identified
- [x] Port conflicts resolved (using 8088 instead of 8080)
- [x] No port collisions with existing services

---

## Step 6.8: Build and Run Container

```bash
cd /home/moein/frigate-intelligence

# Build the Docker image
docker compose build

# Start the container in detached mode
docker compose up -d

# Verify container is running
docker ps | grep frigate-intelligence

# Check container logs for startup errors
docker compose logs -f --tail=50
```

**Expected log output on successful startup:**
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Acceptance Criteria:**
- [x] `docker compose build` completes without errors
- [x] `docker compose up -d` starts the container
- [x] Container status is "Up" in `docker ps`
- [x] Uvicorn logs show "Application startup complete"
- [x] No errors in container logs

---

## Step 6.9: Verify API Accessibility

```bash
# Health check (from server)
curl http://localhost:8088/api/v1/health

# Expected response:
# {"status":"ok","version":"0.1.0","db_connected":true}

# Query test (from server)
curl -X POST http://localhost:8088/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many person events are there?"}'

# From external machine:
curl http://192.168.85.202:8088/api/v1/health
```

**Testing with JSON file (Windows SSH workaround):**

Due to JSON escaping issues in Windows SSH, use a file-based approach:

```bash
# On server, create a JSON file
cat > /tmp/query.json << 'EOF'
{"question": "How many person events are there?"}
EOF

# Post the file
curl -X POST http://localhost:8088/api/v1/query \
  -H "Content-Type: application/json" \
  -d @/tmp/query.json
```

**Acceptance Criteria:**
- [x] `GET /api/v1/health` returns `{"status":"ok","version":"0.1.0","db_connected":true}`
- [x] `POST /api/v1/query` returns SQL + results + explanation
- [x] API is accessible from external machines via `http://192.168.85.202:8088`
- [x] OpenAPI docs available at `http://192.168.85.202:8088/docs`

---

## Step 6.10: Frigate Database Connection

The Frigate database must be accessible inside the container for queries to work.

**Scenario A: Frigate on same server**
- DB path: `/opt/frigate/config/frigate.db`
- Volume mount in docker-compose.yml already handles this

**Scenario B: Frigate on different server**
- Option 1: NFS mount the Frigate config directory
- Option 2: Copy `frigate.db` to this server periodically (not real-time)
- Option 3: Use SSH tunnel / network share

**If DB is missing, API will still start but queries will return errors:**
```json
{
  "question": "How many events?",
  "sql": "",
  "columns": [],
  "rows": [],
  "row_count": 0,
  "explanation": "Failed after 3 attempts. Last error: Execution: Frigate database not found...",
  "attempts": 3,
  "error": "Frigate database not found: /opt/frigate/config/frigate.db"
}
```

**Acceptance Criteria:**
- [x] Container can access `frigate.db` via volume mount
- [x] `db_connected: true` in health check response
- [ ] If Frigate is on a different server, DB is accessible via network mount or copy (pending — user must configure)

---

## Step 6.11: Ongoing Management Commands

```bash
# === Container lifecycle ===
cd /home/moein/frigate-intelligence

# View logs (real-time)
docker compose logs -f

# View last 100 lines of logs
docker compose logs --tail=100

# Restart container
docker compose restart

# Stop container
docker compose down

# Start container
docker compose up -d

# === Rebuild after code changes ===
# Transfer updated files to server, then:
docker compose down
docker compose build --no-cache
docker compose up -d

# === Update .env only (no rebuild needed) ===
# Edit .env on server, then:
docker compose restart

# === Health monitoring ===
# Quick health check
curl http://localhost:8088/api/v1/health

# Check container resource usage
docker stats frigate-intelligence

# Check container status
docker inspect frigate-intelligence --format='{{.State.Status}}'
```

**Acceptance Criteria:**
- [x] Management commands documented
- [x] Rebuild process documented for code updates
- [x] `.env` changes only require restart (no rebuild)

---

## Step 6.12: Firewall Configuration (Optional)

If the Ubuntu server has UFW enabled:

```bash
# Allow port 8088 for API access
sudo ufw allow 8088/tcp

# Allow from specific subnet only (more secure)
sudo ufw allow from 192.168.85.0/24 to any port 8088

# Check firewall status
sudo ufw status
```

**Acceptance Criteria:**
- [ ] Firewall rule added for port 8088 (if UFW is enabled)
- [ ] API accessible from allowed IPs only

---

## Step 6.13: Reverse Proxy (Optional, Recommended for Production)

For production with HTTPS and domain names, use Nginx or Caddy as reverse proxy:

**File: `/etc/nginx/sites-available/frigate-intelligence`**

```nginx
server {
    listen 80;
    server_name intelligence.example.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/frigate-intelligence /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# For HTTPS (using certbot):
sudo certbot --nginx -d intelligence.example.com
```

**Acceptance Criteria:**
- [ ] Nginx reverse proxy configured (optional)
- [ ] HTTPS enabled via certbot (optional)
- [ ] API accessible via domain name (optional)

---

## Final Verification (Phase 6 Complete)

**Run these commands to verify deployment:**

```bash
# 1. Container is running
docker ps | grep frigate-intelligence

# 2. Health check passes
curl http://localhost:8088/api/v1/health
# Expected: {"status":"ok","version":"0.1.0","db_connected":true}

# 3. Query API works
curl -X POST http://localhost:8088/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many person events are there?"}'

# 4. OpenAPI docs accessible
curl http://localhost:8088/docs

# 5. Container auto-restarts
docker compose restart
docker ps | grep frigate-intelligence
```

**Phase 6 Complete When:**
- [x] Dockerfile builds successfully
- [x] `docker-compose.yml` correctly configures ports, volumes, and env
- [x] Container starts and stays running (`restart: unless-stopped`)
- [x] Health endpoint returns `db_connected: true`
- [x] Query endpoint returns SQL + results + explanation
- [x] API accessible from external machines at `http://192.168.85.202:8088`
- [x] OpenAPI docs available at `/docs`
- [x] Management commands documented and tested
- [ ] Frigate DB from remote server connected (pending user configuration)
- [ ] Reverse proxy with HTTPS configured (optional, for production)

---

## Deployment Summary

| Item | Value |
|------|-------|
| Server IP | `192.168.85.202` |
| SSH User | `moein` |
| Project path on server | `/home/moein/frigate-intelligence/` |
| Container name | `frigate-intelligence` |
| External port | `8088` |
| Internal port | `8000` |
| Frigate DB path | `/opt/frigate/config/frigate.db` (mounted read-only) |
| LLM API | `https://api.avalai.ir/v1` |
| LLM Model | `gemini-3.1-flash-lite` |
| Docker network | `frigate-net` (bridge) |
| Restart policy | `unless-stopped` |
