# Phase 7 Advanced Features & Full Docker Deployment — Implementation Report

**Date:** July 19, 2026  
**Server:** `192.168.85.202` (Backend + Frontend)  
**Frigate NVR:** `192.168.85.203`  
**Status:** ✅ All 5 steps completed and deployed

---

## Step 1: Streaming Responses (Backend & Frontend)

### Backend (FastAPI)

**Files Modified:**
- `src/frigate_intelligence/domain/services/llm_service.py` — Added `explain_result_stream()` method to the `LLMService` protocol, returning a `Generator[str, None, None]`.
- `src/frigate_intelligence/infrastructure/llm/avalai_gateway.py` — Implemented `explain_result_stream()` using OpenAI's `stream=True` parameter. Yields token deltas as they arrive from the Avalai API.
- `src/frigate_intelligence/use_cases/text_to_sql/text_to_sql_use_case.py` — Added `TextToSQLStreamResult` dataclass and `execute_streaming()` method. Executes SQL synchronously (with retry logic), then returns a generator for the LLM explanation stream.
- `src/frigate_intelligence/interface_adapters/controllers/api_controller.py` — Added `POST /api/v1/query/stream` endpoint using FastAPI's `StreamingResponse` with `media_type="text/event-stream"`. Sends metadata (SQL, columns, rows) as the first SSE event, then streams explanation chunks, and terminates with `[DONE]`.

**SSE Protocol:**
```
data: {"sql": "...", "columns": [...], "rows": [...], "row_count": N, "error": null}

data: {"chunk": "The query returned..."}

data: {"chunk": " 100 events..."}

data: [DONE]
```

### Frontend (Next.js)

**Files Created/Modified:**
- `src/hooks/use-send-query-stream.ts` — New hook using `fetch()` + `ReadableStream` reader to parse SSE events. Provides `isPending` state and `mutate(question, callbacks)` with `onMeta`, `onChunk`, `onDone`, and `onError` callbacks.
- `src/components/chat/chat-input.tsx` — Replaced `useSendQuery` (mutation) with `useSendQueryStream` (streaming). Creates a placeholder assistant message immediately, then updates its content incrementally as chunks arrive — producing a ChatGPT-like typing effect.

---

## Step 2: UI Polish

### Suggested Prompts

**File Modified:** `src/components/chat-view.tsx`

- Added 4 clickable Persian suggested prompts displayed as pill buttons when the chat is empty:
  - "امروز چند نفر دیده شدند؟"
  - "آخرین رویداد چه زمانی بود؟"
  - "تعداد رویدادها به تفکیک دوربین چیست؟"
  - "پرترفیک‌ترین ساعت روز کدام است؟"
- Clicking a prompt automatically sends the query via a `sendQueryRef` passed from `ChatInput`.
- Added navigation bar with links to Chat (`/`) and Analytics (`/analytics`) pages, with active state highlighting using `usePathname()`.

### Table Overflow

**File Modified:** `src/components/chat/chat-message.tsx`

- Table container wrapped with `max-w-full overflow-x-auto` for horizontal scrolling.
- Added `whitespace-nowrap` to table headers and cells to prevent unwanted wrapping.
- Added `max-w-xs truncate` to cells for long content (e.g., JSON data columns).

---

## Step 3: Vision Integration (Snapshot Rendering)

**File Modified:** `src/components/chat/chat-message.tsx`

- Added `NEXT_PUBLIC_FRIGATE_URL` environment variable (defaults to `http://192.168.85.203:5000`).
- When the SQL result contains an `id` column, a thumbnail image column ("تصویر") is prepended to the table.
- Each row renders an `<img>` tag pointing to `{FRIGATE_URL}/api/events/{eventId}/snapshot.jpg`.
- Images are 64×48px (`w-16 h-12 object-cover rounded`), lazy-loaded, and gracefully hidden on error (404).

---

## Step 4: Analytics Dashboard

### Dependencies
- Installed `recharts@^3.9.2` (38 packages added)

### Files Created

**`src/hooks/use-analytics.ts`**
- React Query `useQuery` hook fetching `GET /api/v1/analytics/summary`
- Supports optional camera filter
- 60-second stale time

**`src/app/analytics/page.tsx`**
- Full analytics dashboard page with:
  - **Stat Cards:** `total_events` (cyan) and `avg_daily_events` (purple) displayed with Persian locale formatting
  - **BarChart:** Events by hour (`events_by_hour` dict → `{hour: "HH:00", count: N}` array)
  - **PieChart:** Events by label (`events_by_label` dict → `{name, value}` array) with 6-color palette and legend
  - Shared header with navigation and `HealthBadge`
  - Loading and error states

---

## Step 5: Dockerization & Deployment

### Next.js Configuration

**`next.config.ts`** — Added `output: "standalone"` for optimized Docker builds.

### Frontend Dockerfile

**`frigate-web-panel/Dockerfile`** — Multi-stage build:
1. **deps** — `node:20-alpine`, `npm ci` for deterministic installs
2. **builder** — Copies source, runs `npx openapi-typescript` to generate API types from live backend, then `npm run build`
3. **runner** — Minimal production image with non-root `nextjs` user, standalone server

**`frigate-web-panel/.dockerignore`** — Excludes `node_modules`, `.next`, `.git`, `.env*.local`, `openapi.json`, `generated.ts`

### Docker Compose (Server)

**`frigate-intelligence/docker-compose.yml`** — Added `frigate-web-panel` service:
```yaml
frigate-web-panel:
  build:
    context: ./frigate-web-panel
    dockerfile: Dockerfile
  container_name: frigate-web-panel
  restart: unless-stopped
  ports:
    - "3000:3000"
  environment:
    - NEXT_PUBLIC_API_URL=http://192.168.85.202:8088
    - NEXT_PUBLIC_FRIGATE_URL=http://192.168.85.203:5000
  depends_on:
    - frigate-intelligence
  networks:
    - frigate-net
```

### Deployment Process

1. Created tar archive of both `frigate-intelligence` and `frigate-web-panel` (excluding `node_modules`, `.next`, `.venv`, etc.)
2. Transferred via `pscp` to `192.168.85.202:/tmp/deploy2.tar`
3. Extracted to `/opt/frigate-intelligence/` (backend source updated, frontend copied)
4. Started backend container first (`docker compose up --build -d frigate-intelligence`)
5. Waited 10s for backend health check to pass
6. Built and started frontend container (`docker compose up --build -d frigate-web-panel`)
7. Verified both containers running with `docker ps`

### Issues Encountered & Resolved

| Issue | Cause | Fix |
|-------|-------|-----|
| `npm ci` sync error | `package-lock.json` out of sync after `recharts` install | Deleted `node_modules` and `package-lock.json`, ran fresh `npm install` |
| `Cannot find module './api/generated'` | `generated.ts` gitignored and excluded from tar | Added `npx openapi-typescript` step in Dockerfile to generate types during build from live backend |

### Final Verification

```
Backend:  http://192.168.85.202:8088/api/v1/health → {"status":"ok","db_connected":true}
Frontend: http://192.168.85.202:3000              → HTTP 200
```

---

## File Change Summary

### Backend (Python)
| File | Change |
|------|--------|
| `domain/services/llm_service.py` | Added `explain_result_stream` to protocol |
| `infrastructure/llm/avalai_gateway.py` | Implemented streaming via OpenAI `stream=True` |
| `use_cases/text_to_sql/text_to_sql_use_case.py` | Added `TextToSQLStreamResult` + `execute_streaming()` |
| `interface_adapters/controllers/api_controller.py` | Added `POST /api/v1/query/stream` SSE endpoint |
| `infrastructure/api/fastapi_app.py` | CORS origins made explicit (localhost + server IP) |
| `docker-compose.yml` | Added `frigate-web-panel` service |

### Frontend (TypeScript/React)
| File | Change |
|------|--------|
| `src/hooks/use-send-query-stream.ts` | **New** — SSE streaming hook |
| `src/hooks/use-analytics.ts` | **New** — Analytics query hook |
| `src/components/chat/chat-input.tsx` | Switched to streaming hook, added `sendQueryRef` |
| `src/components/chat/chat-message.tsx` | Added snapshot thumbnails, table overflow fix |
| `src/components/chat-view.tsx` | Added suggested prompts, navbar, `sendQueryRef` |
| `src/app/analytics/page.tsx` | **New** — Analytics dashboard with Recharts |
| `next.config.ts` | Added `output: "standalone"` |
| `Dockerfile` | **New** — Multi-stage Next.js Docker build |
| `.dockerignore` | **New** |
| `package.json` | Added `recharts` dependency |

---

## Running Services on `192.168.85.202`

| Container | Image | Port | Status |
|-----------|-------|------|--------|
| `frigate-intelligence` | `frigate-intelligence-frigate-intelligence` | `8088→8000` | ✅ Running |
| `frigate-web-panel` | `frigate-intelligence-frigate-web-panel` | `3000→3000` | ✅ Running |

**Network:** `frigate-intelligence_frigate-net` (bridge)

---

## Access URLs

| Service | URL |
|---------|-----|
| Web UI (Chat) | `http://192.168.85.202:3000` |
| Analytics Dashboard | `http://192.168.85.202:3000/analytics` |
| API Health | `http://192.168.85.202:8088/api/v1/health` |
| API Query (SSE) | `http://192.168.85.202:8088/api/v1/query/stream` |
| API Analytics | `http://192.168.85.202:8088/api/v1/analytics/summary` |
| Frigate Snapshots | `http://192.168.85.203:5000/api/events/{id}/snapshot.jpg` |
