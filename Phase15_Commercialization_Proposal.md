# Phase 15: Commercialization — OTA Updates, Orchestration & IP Protection

## Technical Feasibility Proposal

**Date:** 2026-07-22  
**Status:** Draft — Pending Review  
**Target Hardware:** Single-node edge servers (Intel Core i9, dual GPU, 32–64 GB RAM)  
**Current Stack:** Python 3.12 / FastAPI / APScheduler / SQLite / Flutter / Docker Compose / Frigate NVR

---

## 1. Executive Summary

Transform the Frigate Intelligence platform from a development prototype into a commercial **Enterprise Edge Appliance**. The core challenge: once IP is obfuscated and containers are delivered as opaque tarballs, traditional debugging and update workflows become impossible. We must build **lifelines** — robust logging, OTA patching, hardware orchestration, and air-gapped installation — *before* locking down the codebase.

| Sub-Phase | Title | Dependency | Est. Effort |
|-----------|-------|------------|-------------|
| 15.1 | Logging & OTA Update Pipeline | None (foundation) | 3–4 days |
| 15.2 | Backend Orchestrator (Docker Socket) | 15.1 (logging) | 4–5 days |
| 15.3 | IP Protection & Obfuscation | 15.1 (logging replaces CLI debug) | 2–3 days |
| 15.4 | Air-Gapped Installer & Hardware Locking | 15.1 + 15.3 (tarballs exist) | 3–4 days |

**Total estimated effort:** 12–16 development days

---

## 2. Current Architecture Assessment

```
Docker Host (192.168.85.203)
├── Frigate NVR (port 5000) — nginx, go2rtc, config:ro
├── frigate-intelligence (port 8088→8000) — FastAPI, APScheduler, SQLite, data/settings.json
├── frigate-web-panel (port 3000) — Next.js dashboard
└── Network: frigate_default (external)

Mobile Client (Flutter APK)
├── Chat AI (text-to-SQL), Live streaming, NVR playback
├── Settings management (Telegram, scheduling)
└── Persian UI
```

### Current Limitations for Commercialization

1. **Logging:** `logging.basicConfig(stream=sys.stdout)` — no persistent file, no rotation, lost on restart
2. **Updates:** Manual `pscp` + `docker compose up -d --build` — requires SSH + source code
3. **Orchestration:** No Docker Socket integration — cannot discover GPUs or assign containers to hardware
4. **IP Protection:** Source code is plain-text at `/app/src/`; Dockerfile visible; Flutter APK not obfuscated
5. **Deployment:** Requires internet for `docker build`; no offline installer

---

## 3. Feasibility & Tech Stack Assessment

### 3.1 Robust Logging & Debugging Lifeline — ✅ Highly Feasible

**Stack:** Python `logging` with `RotatingFileHandler` → `data/logs/app.log` (already a Docker volume)

- 5 MB per file, 5 backups = 25 MB max
- Structured format with timestamps, module names, levels
- `logging.exception()` captures full stack traces (obfuscated function names post-Phase 15.3)
- New `/api/v1/logs` endpoint exposes recent entries to web panel for remote debugging
- `LOG_LEVEL` configurable via `.env`
- Custom filter redacts API keys and bot tokens from log output

### 3.2 OTA Update Mechanism — ✅ Feasible, Moderate Complexity

**Stack:** FastAPI endpoint + background worker + Docker SDK for Python

**Update Package Format:**
```
update_v1.2.0.tar
├── manifest.json          # version, checksums, min_version
├── images/
│   ├── frigate-intelligence-v1.2.0.tar   # docker save output
│   └── frigate-web-panel-v1.2.0.tar
├── scripts/
│   ├── pre_update.sh      # backup, health check
│   └── post_update.sh     # cleanup, health verification
└── changelog.txt
```

**Update Sequence:**
1. Receive `.tar` → validate SHA-256 checksums → extract to `/tmp/update/`
2. `pre_update.sh`: backup `data/` → `data_backup_YYYYMMDD/`, backup settings, health check
3. Tag current images as `:rollback` → `docker load` new images
4. `docker compose down` (graceful 30s) → `docker compose up -d`
5. `post_update.sh`: health check retry (60s max)
   - **If healthy:** update version, cleanup, log success
   - **If unhealthy:** ROLLBACK — revert to `:rollback` images, restore backup, log event

**Critical Design Decision:** A dedicated `update-agent` sidecar container handles restarts (shares Docker socket, has `data/` access, exposes port 8089). The main container cannot restart itself without killing the API mid-response.

**Web UI:** Settings page → "System Updates" section with drag-drop upload, progress bar, and live status streaming.

### 3.3 Backend Orchestrator — ✅ Feasible, Highest Complexity

**Stack:** Docker SDK for Python + `nvidia-smi` subprocess + `lshw` + `docker-compose.override.yml`

**Hardware Discovery:**
- `nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu,uuid --format=csv,noheader,nounits`
- `/proc/cpuinfo` for CPU topology, `free -h` for memory
- Docker SDK `client.containers.list()` for running containers

**Dynamic Resource Assignment:**
Auto-generates `docker-compose.override.yml`:
```yaml
services:
  frigate:
    cpuset: "0-7"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']
  frigate-intelligence:
    cpuset: "8-15"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['1']
```

**New API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/system/hardware` | CPU, GPU, memory info |
| `GET` | `/api/v1/system/containers` | Container status & resource usage |
| `POST` | `/api/v1/system/assign` | Assign CPU/GPU to containers |
| `GET` | `/api/v1/system/frigate-config` | Get current Frigate config |
| `PUT` | `/api/v1/system/frigate-config` | Update Frigate config (detection delay, etc.) |

**Security:** Docker socket mounted only in `frigate-intelligence`, behind auth. Optional `tecnativa/docker-socket-proxy` for endpoint whitelisting.

### 3.4 IP Protection & Obfuscation — ✅ Feasible, Layered Approach

**Backend — PyArmor (Recommended):**
- Encrypts Python bytecode with runtime decryption
- Multi-stage Dockerfile: build stage obfuscates, production stage ships only `.pyc`
- ~10-15% overhead, no code changes needed
- Alternative: Cython compilation (`.so` files, no overhead, harder to setup)

**Frontend — Flutter Built-in:**
```bash
flutter build apk --release --obfuscate --split-debug-info=./build/symbols
```

**Infrastructure — Container Tarballs:**
```bash
docker save frigate-intelligence:v1.2.0 -o frigate-intelligence-v1.2.0.tar
```
- No Dockerfile shipped, no source code visible
- Combined with PyArmor: even if layers extracted, code is encrypted

**Protection Layers Summary:**

| Layer | Protection | Bypass Difficulty |
|-------|-----------|-------------------|
| Container tarball | No Dockerfile/source — only filesystem layers | Medium |
| PyArmor | Encrypted bytecode, runtime decryption | High |
| Flutter obfuscation | Mangled Dart symbols | Medium |
| Hardware locking | MAC + SHA-256 license hash | Medium |

### 3.5 Air-Gapped Deployment — ✅ Feasible, Makeself + Shell Script

**Deliverable:** `frigate-intelligence-installer-v1.2.0.run` (Makeself self-extracting archive)

**Contents:**
- `install.sh` — prerequisite installation, image loading, startup
- `images/` — docker save tarballs for all services
- `docker-offline-packages/` — Docker CE, NVIDIA Container Toolkit RPMs/DEBs
- `license.lic` — hardware-locked license file
- `docker-compose.yml`, `.env.example`

**`install.sh` Flow:**
1. Verify MAC address against `license.lic` (SHA-256 hash with company secret)
2. Install Docker offline (if not present)
3. Install NVIDIA Container Toolkit (if GPUs detected)
4. `docker load` all image tarballs
5. Create `frigate_default` network
6. `docker compose up -d`
7. Health check (10s sleep + curl `/api/v1/health`)
8. Report success with access URLs

**Hardware Locking:**
- License generated per-customer using MAC address + secret key → SHA-256 hash
- `verify_hardware.sh` recomputes hash and compares — fails if MAC doesn't match
- Future: USB dongle or TPM for stronger binding

---

## 4. Security & Lifecycle Considerations

### 4.1 OTA Update Safety

| Risk | Mitigation |
|------|------------|
| Corrupts settings/data | Auto-backup to `data_backup_YYYYMMDD/` before update |
| New image fails to start | Health check 60s timeout → automatic rollback to `:rollback` |
| Power loss mid-update | `docker compose` is declarative — re-running `up -d` converges |
| Malicious package | SHA-256 checksum verification in `manifest.json` |
| Agent crash mid-update | State persisted to `data/update_state.json` — resumes or rolls back |

### 4.2 Logging Privacy

- Logs must **not** contain LLM prompts (proprietary schema rules) or API keys
- Custom `SensitiveDataFilter` redacts `sk-*`, `aa-*`, bot tokens from log records

---

## 5. Actionable Roadmap

### Sub-Phase 15.1: Logging & OTA Update Pipeline (3–4 days)

| Step | Task | Status |
|------|------|--------|
| 1 | Create `infrastructure/logging_config.py` with `RotatingFileHandler` | Pending |
| 2 | Replace `logging.basicConfig` in `fastapi_app.py` with `setup_logging()` | Pending |
| 3 | Add `LOG_LEVEL` to `settings.py` and `.env` | Pending |
| 4 | Add request logging middleware (correlation ID, response time) | Pending |
| 5 | Create `infrastructure/api/routes/system_routes.py` — log viewer endpoint | Pending |
| 6 | Create `update-agent` sidecar container with Docker socket access | Pending |
| 7 | Implement OTA upload endpoint + background update sequence | Pending |
| 8 | Implement rollback mechanism with health check | Pending |
| 9 | Add "System Updates" section to Flutter settings page | Pending |
| 10 | Tests: logging rotation, OTA upload, rollback scenario | Pending |

### Sub-Phase 15.2: Backend Orchestrator (4–5 days)

| Step | Task | Status |
|------|------|--------|
| 1 | Add `docker` PyPI package to `pyproject.toml` | Pending |
| 2 | Create `infrastructure/orchestrator/hardware_discovery.py` | Pending |
| 3 | Create `infrastructure/orchestrator/container_manager.py` | Pending |
| 4 | Create `infrastructure/orchestrator/compose_override.py` | Pending |
| 5 | Add system routes to `fastapi_app.py` | Pending |
| 6 | Add Frigate config update integration | Pending |
| 7 | Add Docker socket proxy for security | Pending |
| 8 | Add hardware/container widgets to web panel | Pending |
| 9 | Tests: hardware discovery mock, compose override generation | Pending |

### Sub-Phase 15.3: IP Protection & Obfuscation (2–3 days)

| Step | Task | Status |
|------|------|--------|
| 1 | Evaluate PyArmor trial — obfuscate `src/frigate_intelligence/` | Pending |
| 2 | Create multi-stage `Dockerfile.obfuscated` | Pending |
| 3 | Update CI/CD: `flutter build apk --obfuscate --split-debug-info` | Pending |
| 4 | Create `docker save` build script for tarball generation | Pending |
| 5 | Verify obfuscated container passes all tests | Pending |
| 6 | Secure debug symbol storage policy | Pending |

### Sub-Phase 15.4: Air-Gapped Installer & Hardware Locking (3–4 days)

| Step | Task | Status |
|------|------|--------|
| 1 | Create `license_generator.py` (MAC + SHA-256) | Pending |
| 2 | Create `install.sh` with prerequisite detection | Pending |
| 3 | Package offline Docker/NVIDIA RPMs | Pending |
| 4 | Create Makeself `.run` archive builder script | Pending |
| 5 | Test full air-gapped install on clean server | Pending |
| 6 | Test hardware lock bypass scenarios | Pending |
| 7 | Documentation: customer deployment guide | Pending |

---

## 6. Recommendation

Execute sub-phases **in order** — each builds on the previous:

1. **15.1 first** — logging is the foundation; without it, obfuscated code is undebuggable
2. **15.2 second** — orchestrator is independent of obfuscation but needs logging for diagnostics
3. **15.3 third** — obfuscation locks down IP; logging must already be in place
4. **15.4 last** — installer packages the obfuscated tarballs; needs all prior phases complete

**Immediate next step:** Begin Sub-Phase 15.1 by creating `infrastructure/logging_config.py` and replacing the basic logging in `fastapi_app.py`.
