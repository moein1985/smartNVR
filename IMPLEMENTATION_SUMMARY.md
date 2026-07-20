# Implementation Summary — Frigate Intelligence Platform

**Date:** July 20, 2026  
**Status:** Production-deployed across all three components  
**Target Server:** `192.168.85.203`

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Production Server                      │
│                   192.168.85.203                          │
│                                                           │
│  ┌─────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │   Frigate   │  │ frigate-         │  │ frigate-web  │ │
│  │   NVR       │  │ intelligence     │  │ -panel       │ │
│  │   (Docker)  │  │ (Docker)         │  │ (Docker)     │ │
│  │             │  │                  │  │              │ │
│  │ Port 5000   │  │ Port 8088→8000   │  │ Port 3000    │ │
│  │ Port 8554   │  │ FastAPI + Uvicorn│  │ Next.js 16   │ │
│  │ Port 8555   │  │ Python 3.12      │  │ Node 20      │ │
│  └──────┬──────┘  └────────┬─────────┘  └──────┬───────┘ │
│         │                  │                   │          │
│         │ SQLite DB        │ /opt/frigate/     │          │
│         │ /opt/frigate/    │ config/frigate.db │          │
│         │ config/frigate.db│ (mounted ro)      │          │
│         │ (read-only)      │                   │          │
│         │                  │ settings.json     │          │
│         │                  │ (persisted)       │          │
│  └──────┴──────────────────┴───────────────────┴────────┘ │
│                                                           │
│  Network: frigate_default (external Docker network)       │
└─────────────────────────────────────────────────────────┘
         ▲                                    ▲
         │                                    │
    ┌────┴────┐                         ┌─────┴─────┐
    │ Flutter │                         │  Browser  │
    │ Android │                         │  (Web)    │
    │ App     │                         │           │
    └─────────┘                         └───────────┘
```

---

## 2. Component Details

### 2.1 Backend — `frigate-intelligence` (Python / FastAPI)

**Location:** `frigate-intelligence/`  
**Docker container:** `frigate-intelligence`  
**Port mapping:** `8088 → 8000` (host → container)  
**Python version:** 3.12  
**Framework:** FastAPI + Uvicorn  
**LLM provider:** Avalai.ir (OpenAI-compatible API)  
**Default model:** `gemini-3.1-flash-lite`

**Key dependencies:**
- `fastapi`, `uvicorn[standard]` — REST API
- `openai`, `langchain`, `langchain-openai` — LLM integration
- `pydantic`, `pydantic-settings` — Validation
- `httpx` — Async HTTP for bot notifications
- `apscheduler` — Cron-based scheduled reports
- `typer`, `rich` — CLI interface

**Project structure (Clean Architecture):**
```
src/frigate_intelligence/
├── config/
│   ├── settings.py          # Pydantic Settings (.env-based)
│   └── dependencies.py      # DI Container
├── domain/
│   ├── entities/            # Event, Recording, QueryResult, Notification, etc.
│   ├── repositories/        # FrigateRepository Protocol
│   ├── services/            # LLMService, NotifierService Protocols
│   ├── value_objects/       # SQLQuery, PromptContext, TimeRange
│   └── models/
│       └── settings_model.py  # Pydantic SettingsModel (settings.json)
├── use_cases/
│   ├── text_to_sql/         # TextToSQLUseCase, SQLValidator, PromptBuilder
│   ├── correlate_pos/       # POS correlation use case
│   └── send_notification/   # Notification dispatch
├── interface_adapters/
│   ├── controllers/
│   │   └── api_controller.py  # REST endpoints
│   ├── presenters/
│   │   └── api_presenter.py
│   └── schemas/
│       ├── api_models.py      # Pydantic API models
│       └── frigate_schema.py  # DB schema context for LLM
├── infrastructure/
│   ├── api/
│   │   ├── fastapi_app.py     # App factory
│   │   └── routes/            # event_routes, pos_routes, analytics_routes
│   ├── database/
│   │   ├── frigate_sqlite_gateway.py
│   │   └── connection.py
│   ├── llm/
│   │   └── avalai_gateway.py
│   ├── notifiers/
│   │   ├── telegram_notifier.py
│   │   └── bale_notifier.py
│   ├── notifications/
│   │   └── bot_service.py     # BotNotificationService (httpx-based)
│   ├── config/
│   │   └── settings_manager.py  # SettingsManager (JSON persistence)
│   ├── scheduler/
│   │   └── cron_service.py      # CronService (APScheduler)
│   ├── pos/
│   │   └── pos_api_gateway.py
│   └── cli/
│       └── cli_app.py
├── main.py                   # CLI entry point (Typer)
└── server.py                 # Direct uvicorn launcher
```

**API endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/query` | Natural language → SQL → results + explanation |
| POST | `/api/v1/query/stream` | Streaming version of query (SSE) |
| GET | `/api/v1/health` | Health check (status, version, DB connected) |
| GET | `/api/v1/events` | List events (filter by camera, label) |
| GET | `/api/v1/settings` | Get current settings (from `settings.json`) |
| POST | `/api/v1/settings` | Save settings to `settings.json` |
| GET | `/api/v1/analytics/...` | Analytics endpoints |
| GET | `/api/v1/pos/...` | POS correlation endpoints |
| GET | `/openapi.json` | OpenAPI schema (used by Next.js codegen) |

**Settings persistence:** `settings.json` file (managed by `SettingsManager`)
- Fields: `avalai_api_key`, `llm_model`, `telegram_enabled`, `telegram_bot_token`, `telegram_chat_id`, `bale_enabled`, `bale_bot_token`, `bale_chat_id`, `report_frequency`, `report_target`

---

### 2.2 Web Panel — `frigate-web-panel` (Next.js)

**Location:** `frigate-web-panel/`  
**Docker container:** `frigate-web-panel`  
**Port mapping:** `3000 → 3000`  
**Framework:** Next.js 16 (App Router, Turbopack)  
**Node version:** 20 (Alpine)  
**Styling:** TailwindCSS  
**Data fetching:** React Query (TanStack), openapi-fetch  
**Language:** Persian (RTL), `lang="fa"`

**Environment variables (Docker):**
- `NEXT_PUBLIC_API_URL=http://192.168.85.203:8088`
- `NEXT_PUBLIC_FRIGATE_URL=http://192.168.85.203:5000`

**Pages:**
| Route | Description |
|-------|-------------|
| `/` | Chat UI (natural language queries with streaming) |
| `/analytics` | Analytics dashboard (charts, summaries) |
| `/settings` | Settings dashboard (AI config, bot integration, cron reports) |

**Key components:**
- `chat-view.tsx` — Chat interface with streaming responses
- `chat-input.tsx`, `chat-message.tsx` — Chat sub-components
- `health-badge.tsx` — Backend health indicator
- `settings-api.ts` — Settings API client (`getSettings()`, `updateSettings()`)

**API client:** Auto-generated TypeScript types from FastAPI OpenAPI spec via `openapi-typescript` (during Docker build step).

---

### 2.3 Flutter App — `frigate_app`

**Location:** `frigate_app/`  
**Package:** `com.frigate.frigate_intelligence`  
**Target device:** Android (Samsung SM-S938B, USB-connected)  
**Framework:** Flutter (Material 3 Expressive)  
**State management:** Riverpod  
**HTTP client:** Dio  

**Project structure:**
```
lib/
├── main.dart
├── core/
│   ├── config/
│   │   ├── app_config.dart           # ServerConfig (ip, port, isMockMode)
│   │   └── server_config_service.dart # SharedPreferences persistence
│   └── theme/
│       └── app_theme.dart
├── data/
│   └── datasources/
│       ├── api_client.dart           # ApiClient (Dio-based, real server)
│       └── mock_api_client.dart      # MockApiClient (offline test data)
├── presentation/
│   ├── pages/
│   │   ├── chat_page.dart            # Main chat screen
│   │   └── settings_page.dart        # Server config (IP, port, mock toggle)
│   ├── providers/
│   │   ├── chat_provider.dart        # ChatNotifier, ChatMessage, ChatState
│   │   └── server_config_provider.dart # Riverpod providers for config + API client
│   └── widgets/
│       ├── chat_bubble.dart          # Message rendering + event gallery
│       └── event_image.dart          # (reserved for future use)
```

**Mock mode:** When `isMockMode == true`, `MockApiClient` returns hardcoded test data (2 mock events with picsum.photos images). When `false`, `ApiClient` sends real HTTP requests to the configured server.

**Image URL logic (chat_bubble.dart):**
- Mock mode: `https://picsum.photos/seed/$eventId/400/300`
- Real mode: `http://${serverIp}:5000/api/events/${eventId}/snapshot.jpg`
- Error fallback: `Icon(Icons.broken_image)` (not picsum)

**Row parsing (chat_provider.dart):**
- Backend returns `rows` as `list[list[Any]]` (array of arrays)
- `eventRows` getter zips `columns` with each row to produce `List<Map<String, dynamic>>`
- Handles both List-rows (real API) and Map-rows (mock API) gracefully

---

### 2.4 Frigate NVR

**Docker container:** `frigate`  
**Image:** `ghcr.io/blakeblackshear/frigate:0.18.0-beta1-tensorrt`  
**Ports:** `5000` (Web UI/API), `8554` (RTSP), `8555` (WebRTC)  
**GPU:** NVIDIA (TensorRT)  
**Config file:** `/opt/frigate/config/config.yml`  
**Database:** `/opt/frigate/config/frigate.db` (SQLite, ~5.9 MB)  
**Media storage:** `/mnt/record50/frigate`  
**Camera:** `cam1` (RTSP: `192.168.85.112`, Hikvision)  
**Model:** YOLOv9-t-320 (ONNX, 320×320, RGB, NCHW)  

---

## 3. Port Map

| Service | Host Port | Container Port | Protocol |
|---------|-----------|----------------|----------|
| Frigate NVR | 5000 | 5000 | HTTP |
| Frigate RTSP | 8554 | 8554 | RTSP |
| Frigate WebRTC | 8555 | 8555 | TCP/UDP |
| Backend API | 8088 | 8000 | HTTP |
| Web Panel | 3000 | 3000 | HTTP |

---

## 4. Docker Compose (Production)

**File:** `/home/moein/frigate-intelligence/docker-compose.yml`

```yaml
services:
  frigate-intelligence:
    build: ./frigate-intelligence
    ports: ["8088:8000"]
    volumes: ["/opt/frigate/config:/opt/frigate/config:ro"]
    env_file: ./frigate-intelligence/.env
    networks: [frigate_default]

  frigate-web-panel:
    build: ./frigate-web-panel
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://192.168.85.203:8088
      - NEXT_PUBLIC_FRIGATE_URL=http://192.168.85.203:5000
    depends_on: [frigate-intelligence]
    networks: [frigate_default]

networks:
  frigate_default:
    external: true
```

---

## 5. Environment Logic (Mock vs. Real)

### Flutter App
- **Mock mode:** `MockApiClient` returns hardcoded data, images from `picsum.photos`
- **Real mode:** `ApiClient` (Dio) sends HTTP to `http://<serverIp>:<port>`, images from Frigate port 5000
- **Toggle:** Settings page in Flutter app (`isMockMode` flag stored in `SharedPreferences`)
- **Server IP/port:** User-configurable via Settings page, persisted locally

### Web Panel
- **API URL:** Set via `NEXT_PUBLIC_API_URL` environment variable (baked at build time)
- **Frigate URL:** Set via `NEXT_PUBLIC_FRIGATE_URL` environment variable
- **No mock mode** — always connects to real backend

### Backend
- **LLM API key:** Stored in `settings.json` (managed via `/api/v1/settings` endpoint)
- **DB path:** Mounted read-only from `/opt/frigate/config/frigate.db`
- **Bot tokens:** Stored in `settings.json`, used by `BotNotificationService`

---

## 6. Architectural Pivots & Adaptations

### 6.1 Settings Management: `.env` → `settings.json` via API
- **Original plan (Phase 1):** Settings via `.env` file and `pydantic-settings`
- **Actual implementation:** Added `SettingsManager` (JSON file persistence) + `SettingsModel` (Pydantic) + REST endpoints (`GET/POST /api/v1/settings`)
- **Reason:** Web panel needed a UI to dynamically configure API keys, bot tokens, and report schedules without restarting the backend
- **Impact:** New directories `infrastructure/config/`, `domain/models/`; `APIController` extended with settings routes

### 6.2 Flutter `MockApiClient` Implementation
- **Original plan (Phase 4):** Direct API connection only
- **Actual implementation:** Added `MockApiClient` with hardcoded test data for offline development/testing
- **Reason:** Allow Flutter UI development without a running backend; test layout and rendering before server was available
- **Impact:** `server_config_provider.dart` switches between `MockApiClient` and `ApiClient` based on `isMockMode` flag

### 6.3 Frigate Safe Mode — `clean_copy` Fix
- **Issue:** Frigate entered Safe Mode with error: `Line 49: snapshots -> clean_copy - Extra inputs are not permitted`
- **Root cause:** `clean_copy` parameter was removed in Frigate 0.18.x but still present in `config.yml`
- **Fix:** Removed `clean_copy: true` line from `/opt/frigate/config/config.yml` on production server
- **Impact:** Frigate restarted successfully with snapshots enabled (without `clean_copy`)

### 6.4 Flutter Row Parsing — List-of-Lists vs. List-of-Maps
- **Issue:** App crashed with Red Screen of Death when receiving real API responses
- **Root cause:** Backend returns `rows` as `list[list[Any]]` (arrays), but Flutter code cast to `Map<String, dynamic>`
- **Fix:** `eventRows` getter in `chat_provider.dart` now zips `columns` array with each row list to produce maps
- **Impact:** Handles both real API (list-rows) and mock API (map-rows) transparently

### 6.5 Flutter Image URL — Hardcoded IP → Dynamic Server IP
- **Issue:** Event gallery showed random images (e.g., airplane) instead of real camera snapshots
- **Root cause:** Image URL was hardcoded to `http://192.168.85.203:5000/...` and `errorBuilder` fell back to `picsum.photos`
- **Fix:** Pass `serverIp` from `serverConfigProvider` through `ChatBubble` to `_EventGallery`; use `http://$serverIp:5000/...` for real mode; `errorBuilder` shows `broken_image` icon instead of picsum fallback
- **Impact:** Real camera snapshots now load correctly; broken snapshots show proper error icon

### 6.6 Backend Port: 8000 → 8088
- **Original plan:** Backend on port 8000
- **Actual implementation:** Container exposes 8000, Docker maps to host 8088 (to avoid conflicts)
- **Reason:** Port 8000 was in use on staging server (202); kept 8088 for production consistency

### 6.7 Web Panel: localStorage → API-backed Settings
- **Original plan:** Settings page with `localStorage` persistence and mock save (toast only)
- **Actual implementation:** Created `settings-api.ts` with `getSettings()` and `updateSettings()` calling real backend endpoints
- **Reason:** Settings need to persist on the server (shared with backend cron jobs and bot services)
- **Impact:** Settings page now fetches on mount, shows loading skeleton, and saves to `settings.json` via API

---

## 7. Phase Completion Status

| Phase | Title | Status | Notes |
|-------|-------|--------|-------|
| Phase 1 | CLI Text-to-SQL Agent | ✅ Completed | Clean Architecture, Typer CLI, Avalai LLM |
| Phase 2 | REST API (FastAPI) | ✅ Completed | All endpoints live on port 8088 |
| Phase 3 | Messaging Bots (Telegram + Bale) | ✅ Completed | Notifiers + BotNotificationService (httpx) |
| Phase 4 | Flutter Client | ✅ Completed | Android app with mock/real mode, chat UI, event gallery |
| Phase 5 | POS Integration & Analytics | ✅ Completed | POS correlation + analytics routes |
| Phase 6 | Server Deployment (Docker) | ✅ Completed | Dockerized backend on 202 → migrated to 203 |
| Phase 7 | Web UI (Next.js) | ✅ Completed | Chat, Analytics, Settings pages |
| Phase 8 | Production Deployment (203) | ✅ Completed | All 3 containers running on production server |

---

## 8. Current Production URLs

| Service | URL |
|---------|-----|
| Frigate NVR | `http://192.168.85.203:5000` |
| Backend API | `http://192.168.85.203:8088` |
| Web Panel | `http://192.168.85.203:3000` |
| Settings API | `http://192.168.85.203:8088/api/v1/settings` |
| Health Check | `http://192.168.85.203:8088/api/v1/health` |
| Frigate Snapshots | `http://192.168.85.203:5000/api/events/<id>/snapshot.jpg` |
