# Bug Fixing Discipline — Frigate NVR Project

**Version:** 1.0  
**Date:** July 20, 2026  
**Applies to:** `frigate-intelligence` (Python/FastAPI/SQLite backend) and `frigate_app` (Flutter/Riverpod mobile app)

---

## 1. Regression-First Principle

**Never fix anything without first confirming the existing test suite passes.**

### Backend (frigate-intelligence)

```bash
cd frigate-intelligence
python -m pytest tests/ -v --tb=short
```

- Test directory: `tests/unit/`, `tests/integration/`, `tests/e2e/`
- Key test files: `test_text_to_sql_use_case.py`, `test_sql_validator.py`, `test_api.py`, `test_frigate_sqlite_gateway.py`, `test_analytics_use_case.py`, `test_correlate_pos_use_case.py`
- **Rule:** Test count must never decrease. If a test is removed, it must be replaced with an equivalent or stronger test.

### Frontend (frigate_app)

```bash
cd frigate_app
flutter test
```

- Test directory: `test/`
- Current test: `widget_test.dart` (Chat page smoke test)
- **Rule:** `flutter test` must pass with zero failures before any fix is merged.

### Pre-Fix Baseline

Record the baseline output before making changes:

```bash
# Backend
python -m pytest tests/ --co -q | wc -l    # Record test count

# Frontend
flutter test --reporter compact 2>&1 | tail -1   # Record pass/fail summary
```

If the baseline is already red, fix the failing tests first or document why they are failing before proceeding.

---

## 2. Reproduce Before Fixing

**A bug that cannot be reproduced cannot be verified as fixed.**

### Required Steps

1. **Document the reproduction steps** in the Bug Registry (Section 7) before writing any fix code.
2. **Capture the error output:**
   - Backend: Full traceback from `uvicorn` logs or `pytest` output.
   - Frontend: `adb logcat -s flutter:I` output or `flutter run --verbose` console output.
3. **Note the environment:**
   - Frigate server IP and port (e.g., `192.168.85.203:5000`)
   - Camera name (e.g., `cam1`)
   - Device ID (e.g., `R5CY23R9DXR` — Samsung SM-S938B)
   - Docker container status (`docker ps`)

### Reproduction Commands

```bash
# Backend API reproduction
curl -s -X POST http://192.168.85.203:8088/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "<reproduce question>"}' | python -m json.tool

# Frontend log capture
adb -s R5CY23R9DXR logcat -c
adb -s R5CY23R9DXR logcat -s flutter:I AndroidRuntime:E *:F

# Frigate API verification
curl -s http://192.168.85.203:5000/api/<endpoint> | python -m json.tool

# go2rtc stream check
curl -s http://192.168.85.203:5000/api/go2rtc/streams | python -m json.tool
```

**Do not proceed to the fix until reproduction is confirmed.**

---

## 3. Regression Test Required

Every bug fix must include a regression test that would fail without the fix and pass with it.

### Test Categories

| Category | Location | Framework | Example |
|----------|----------|-----------|---------|
| **Text-to-SQL Parsing** | `tests/unit/use_cases/test_text_to_sql_use_case.py` | `pytest` | Test that a malformed question returns a graceful error, not a crash |
| **SQL Validator** | `tests/unit/use_cases/test_sql_validator.py` | `pytest` | Test that forbidden SQL operations (DROP, DELETE) are rejected |
| **API Endpoints** | `tests/integration/test_api.py` | `pytest` + `TestClient` | Test that `/api/v1/query` returns 200 with valid payload, 422 with invalid |
| **SQLite Gateway** | `tests/integration/test_frigate_sqlite_gateway.py` | `pytest` | Test that query results map correctly to `QueryResult` entity |
| **Analytics** | `tests/unit/use_cases/test_analytics_use_case.py` | `pytest` | Test that analytics aggregation handles empty result sets |
| **POS Correlation** | `tests/unit/use_cases/test_correlate_pos_use_case.py` | `pytest` | Test that POS correlation handles missing camera zones |
| **Domain Entities** | `tests/unit/domain/` | `pytest` | Test entity validation and factory methods |
| **Interface Adapters** | `tests/unit/interface_adapters/` | `pytest` | Test controller-to-use-case wiring |
| **Flutter Widget/UI** | `frigate_app/test/` | `flutter_test` | Test that `LiveViewTab` renders camera grid, `PlaybackTab` shows timeline |
| **Streaming/Playback** | `frigate_app/test/` | `flutter_test` | Test that `LiveStreamController` constructs correct RTSP URL, `PlaybackTab` constructs correct clip.mp4 URL |
| **E2E** | `tests/e2e/` | `pytest` | Full pipeline test: question → SQL → execution → response |

### Regression Test Naming Convention

```python
# Backend (pytest)
def test_bug_<ID>_<short_description>():
    """Regression test for BUG-<ID>: <description>"""
    ...

# Frontend (flutter_test)
testWidgets('bug_<ID>_<short_description>', (tester) async {
  // Regression test for BUG-<ID>: <description>
});
```

---

## 4. Minimal Change Principle

**Fix the root cause. No unrelated refactoring. No drive-by improvements.**

### Rules

1. **One bug per commit.** If you discover a second bug while fixing the first, log it and fix it separately.
2. **No cosmetic changes.** Do not reformat, rename, or restructure code that is not directly related to the bug.
3. **Root cause, not symptom.** If the API returns wrong data, fix the query/gateway, not the response formatter.
4. **Preserve existing architecture.** Follow the Clean Architecture layering:
   - `domain/` — Entities, no external dependencies
   - `use_cases/` — Business logic, depends on domain only
   - `interface_adapters/` — Controllers, presenters
   - `infrastructure/` — FastAPI app, SQLite gateway, Frigate API client
5. **No new dependencies.** If a fix requires a new package, justify it explicitly.

### Example

```python
# BAD: Fixing a SQL injection by wrapping the output in a try/except
def execute_query(self, sql: str) -> QueryResult:
    try:
        return self.gateway.execute(sql)
    except Exception:
        return QueryResult.empty()  # Hides the real problem

# GOOD: Fix the SQL validator to reject the injection pattern
class SQLValidator:
    FORBIDDEN_PATTERNS = [r";\s*DROP", r";\s*DELETE", ...]
    def validate(self, sql: str) -> bool:
        return not any(re.search(p, sql, re.I) for p in self.FORBIDDEN_PATTERNS)
```

---

## 5. No Silent Failures

**Every error must be visible. No empty catches, no swallowed exceptions, no silent fallbacks.**

### Backend (Python)

```python
import logging

logger = logging.getLogger(__name__)

# BAD
try:
    result = await use_case.execute(question)
except Exception:
    return {"error": "Something went wrong"}  # What went wrong?

# GOOD
try:
    result = await use_case.execute(question)
except ValueError as e:
    logger.warning("Invalid query input: %s", e, exc_info=True)
    return JSONResponse(status_code=422, content={"detail": str(e)})
except Exception as e:
    logger.error("Unexpected error in query execution: %s", e, exc_info=True)
    raise  # Let FastAPI's exception handler produce a proper 500
```

### Frontend (Flutter)

```dart
// BAD
try {
  await controller.startStream();
} catch (e) {
  // silently ignored
}

// GOOD
try {
  await controller.startStream();
} catch (e) {
  debugPrint('[Live] Failed to start stream for $cameraName: $e');
  setState(() {
    _statuses[cameraName] = StreamStatus.error;
    _errors[cameraName] = e.toString();
  });
}
```

### Logging Conventions

| Component | Prefix | Example |
|-----------|--------|---------|
| Live streaming | `[Live]` | `[Live] Starting RTSP stream: rtsp://...` |
| Playback | `[Playback]` | `[Playback] Opening URL: http://...` |
| WebRTC (legacy) | `[WebRTC]` | `[WebRTC] WebSocket connected` |
| API client | `[API]` | `[API] GET /api/v1/cameras → 200` |
| Frigate API | `[Frigate]` | `[Frigate] go2rtc streams: {cam1: ...}` |

---

## 6. Deployment Checklist

Before deploying any change, **all** of the following must pass:

### Backend

```bash
cd frigate-intelligence

# 1. Lint
ruff check src/ tests/

# 2. Tests
python -m pytest tests/ -v --tb=short

# 3. Type check (if mypy is configured)
mypy src/frigate_intelligence/
```

### Frontend

```bash
cd frigate_app

# 1. Static analysis — MUST be zero issues
flutter analyze

# 2. Tests
flutter test

# 3. Build
flutter build apk --debug
```

### Docker / Server

```bash
# 1. Container health
docker ps --filter "name=frigate" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Frigate API reachable
curl -s http://192.168.85.203:5000/api/config | python -m json.tool > /dev/null && echo "Frigate OK"

# 3. go2rtc streams configured
curl -s http://192.168.85.203:5000/api/go2rtc/streams | python -m json.tool

# 4. Backend API reachable
curl -s http://192.168.85.203:8088/health | python -m json.tool

# 5. RTSP restream accessible
# (Test from device or machine with network access to server)
Test-NetConnection -ComputerName 192.168.85.203 -Port 8554
```

### Deployment Gate

| Check | Command | Required Result |
|-------|---------|-----------------|
| Backend lint | `ruff check src/ tests/` | 0 errors |
| Backend tests | `python -m pytest tests/` | All pass, count ≥ baseline |
| Flutter analyze | `flutter analyze` | 0 issues |
| Flutter tests | `flutter test` | All pass |
| Flutter build | `flutter build apk --debug` | Success |
| Frigate API | `curl /api/config` | 200 OK |
| go2rtc streams | `curl /api/go2rtc/streams` | Streams present |
| Backend API | `curl /health` | 200 OK |
| RTSP port | `Test-NetConnection 8554` | True |

**If any check fails, deployment is blocked.**

---

## 7. Bug Registry

Log every bug discovered and fixed in this table. Append new rows at the bottom.

| ID | Date | Description | Root Cause | Fix | Regression Test | Status |
|----|------|-------------|------------|-----|-----------------|--------|
| — | — | — | — | — | — | — |
| FEAT-011 | 2026-07-21 | LLM cannot query recognized person names; EventItem API lacks sub_label | `frigate_schema.py` missing sub_label rules; `api_models.py` missing sub_label field | Added 5 sample queries + 5 SQL rules for sub_label disambiguation; added sub_label to EventItem | `test_api_models_sub_label.py`, `test_frigate_schema_sub_label.py` | Verified |
| BUG-016 | 2026-07-21 | CompreFace UI returns 502 Bad Gateway; compreface-core in crash loop | Java 11 NullPointerException in CgroupV2Subsystem due to modern Linux cgroups v2; also external DB volume mount overwrote internal PostgreSQL pre-built data | Added `ADMIN_JAVA_OPTS=-XX:-UseContainerSupport` and `API_JAVA_OPTS=-XX:-UseContainerSupport` to compreface-core environment; removed external compreface-db volume mount so CompreFace uses its internal PostgreSQL | Manual verification of container logs and UI accessibility | Verified |
| BUG-017 | 2026-07-21 | Android app cannot load cameras from local network server (192.168.85.203) | Android blocks cleartext HTTP traffic by default (API 28+); app uses plain HTTP to Frigate server on local network | Added `android:usesCleartextTraffic="true"` to `<application>` tag in AndroidManifest.xml | `bug_017_rtsp_url_construction` in `regression_test.dart` | Fixed |
| BUG-018 | 2026-07-21 | flutter_webrtc dependency adds unnecessary native libs and build complexity; not used in any Dart code | Dead dependency from earlier WebRTC streaming experiment; replaced by RTSP via media_kit | Removed `flutter_webrtc` from pubspec.yaml; replaced `media_kit_libs_android_video` with unified `media_kit_libs_video` (bundles native libs for Android, iOS, Windows, macOS, Linux) | `flutter pub get` succeeded; `flutter analyze` zero issues | Fixed |
| BUG-019 | 2026-07-21 | PlaybackTab initializes Player inside build() method causing potential rebuild issues | Anti-pattern: `if (_player == null) { _initPlayer(); }` in build() instead of initState() | Moved `_initPlayer()` call to `initState()`; removed lazy init from `build()`; changed `_initPlayer()` from `Future<void>` to `void` | Code review verified; `flutter analyze` zero issues; media_kit Player requires native libs not available in flutter_test | Fixed |
| BUG-020 | 2026-07-21 | MainScaffold only had 2 nav items (AI, NVR); Settings not accessible from bottom nav | Original scaffold lacked Settings tab; settings only reachable via ChatPage app bar icon | Rewrote MainScaffold with 3 nav items (AI, NVR, Settings) and adaptive LayoutBuilder (BottomNavigationBar < 600px, NavigationRail >= 600px) | `bug_020_bottom_nav_has_three_items`, `bug_020_settings_tab_navigates_to_settings_page` in `regression_test.dart` | Fixed |
| BUG-021 | 2026-07-21 | Existing widget_test.dart fails after MainScaffold update (settings_outlined icon count changed) | `findsOneWidget` assertion for `Icons.settings_outlined` now finds 2 (ChatPage app bar + BottomNavigationBar) | Updated assertion to `findsNWidgets(2)` in `widget_test.dart` | `flutter test` all 4 tests pass | Fixed |
| BUG-022 | 2026-07-21 | Android app shows no cameras in Live tab; /api/v1/cameras returns empty array | frigate-intelligence container on `frigate_default` Docker network cannot resolve hostname `frigate` which is on `frigate_frigate_net` network; DNS lookup fails with "Name or service not known" | Changed `api_controller.py` line 141 from `http://frigate:5000/api/config` to `http://192.168.85.203:5000/api/config` (host IP); deployed to all 3 paths in container; restarted container | `curl -s http://192.168.85.203:8088/api/v1/cameras` returns 1 camera (cam1) | Fixed |
| BUG-023 | 2026-07-21 | Server health endpoint lacks timestamp/timezone info; LLM cannot resolve client-local time expressions (e.g. "9am today") correctly because SQLite `localtime` = UTC on server, not client timezone | `HealthResponse` model had no timestamp fields; `QueryRequest` had no client timezone fields; LLM prompt had no time context, causing `datetime(start_time, 'unixepoch', 'localtime')` to resolve to UTC instead of client's Asia/Tehran (+03:30) | Added `server_timestamp`, `server_timezone`, `server_datetime_iso` to `HealthResponse`; added `client_timezone`, `client_offset_minutes`, `client_timestamp` to `QueryRequest`; added `time_context` field to `PromptContext`; `PromptBuilder.build()` now accepts `client_tz_info` dict and computes absolute UTC timestamps + injects "Current Time Context" section into LLM system prompt with explicit warning not to use `localtime` for client TZ; `TextToSQLUseCase.execute()` and `execute_streaming()` rebuild prompt with TZ context when `client_tz_info` is provided | `test_bug_023_health_endpoint_returns_timestamp`, `test_bug_023_query_accepts_client_timezone` in `tests/integration/test_api.py` | Fixed |
| BUG-024 | 2026-07-21 | Flutter app has no clock skew detection; user queries with relative time expressions ("today", "last hour") produce wrong results if device clock differs from server by >2 min | No `TimeSyncNotifier` existed; `ApiClient.query()` did not send client timezone info; `MainScaffold` had no skew warning UI | Created `time_sync_provider.dart` with `TimeSyncNotifier` that calls `health()` on startup + every 5 min, calculates `skew = client_time - server_time`, exposes `hasSignificantSkew` (>2 min); updated `api_client.dart` `query()` to inject `client_timezone`, `client_offset_minutes`, `client_timestamp` into POST body; updated `main_scaffold.dart` to wrap body in `Column` with conditional `MaterialBanner` showing skew warning + Retry button; updated `mock_api_client.dart` health() to include timestamp fields; updated existing tests to override `apiClientProvider` with mock | `bug_024_time_sync_banner_shows_on_skew`, `bug_024_time_sync_no_banner_when_synced` in `test/regression_test.dart` | Fixed |
| BUG-025 | 2026-07-21 | LLM model `gemini-3.1-flash-lite` lacks JSON mode support; 20 verbose SQL rules with repetitive sub_label rules (16-20) bloat prompt; `_enrich_question()` hack injects schema hints into user question unnecessarily | Old model limited in capability; schema rules were accumulated incrementally causing redundancy; `_enrich_question()` was a workaround for the old model's inability to follow schema rules about sub_label | Changed `llm_model` default to `gemini-2.5-flash` in `settings.py` and `settings_model.py`; added `classify_intent()` (JSON mode) and `smart_query()` (unified intent+SQL) to `avalai_gateway.py` and `llm_service.py` protocol; consolidated 20 SQL rules → 13 clean rules in `frigate_schema.py` (removed repetitive sub_label rules 16-20 → single rule 13; removed rule 11 forcing `id` column); removed `_enrich_question()` entirely from `text_to_sql_use_case.py` — raw user question now passed directly to LLM | `test_bug_025_llm_model_upgrade_sql_generation`, `test_bug_025_enrich_question_removed` in `tests/unit/use_cases/test_text_to_sql_use_case.py` | Fixed |
| BUG-026 | 2026-07-21 | Backend cannot distinguish playback requests from event queries; "show video 9am-9:30am" executes SQL against DB instead of returning playback intent for frontend deep linking | `TextToSQLUseCase.execute()` always called `generate_sql()` and ran SQL against DB — no intent classification; `QueryResponse` had no `intent` or `playback_intent` fields; streaming response lacked intent metadata | Added `PlaybackIntent` model to `api_models.py`; added `intent` and `playback_intent` fields to `QueryResponse`; rewrote `execute()` and `execute_streaming()` to call `smart_query()` first — if `intent == 'playback_query'`, skips SQL execution and returns `PlaybackIntent` dict with camera/start_time/end_time/date; if `intent == 'event_query'`, uses returned SQL on attempt 1 and falls back to `generate_sql()` for retries; added `_build_playback_intent()` helper to parse ISO timestamps to Unix epoch; updated `api_presenter.py` to map `PlaybackIntent` model; updated `api_controller.py` streaming meta to include `intent` and `playback_intent` | `test_bug_026_playback_intent_classification`, `test_bug_026_event_intent_still_works` in `tests/integration/test_api.py` | Fixed |

### Status Values

- **Open:** Bug discovered, not yet fixed.
- **In Progress:** Fix being implemented.
- **Fixed:** Fix merged, regression test added.
- **Verified:** Fix confirmed on device/server.
- **Wontfix:** Bug accepted as known limitation (requires justification).

### Example Entry

| ID | Date | Description | Root Cause | Fix | Regression Test | Status |
|----|------|-------------|------------|-----|-----------------|--------|
| BUG-001 | 2026-07-20 | Live stream shows black screen, no video | go2rtc stream not configured on server; WebRTC ICE candidates missing | Switched from WebRTC to RTSP restream via go2rtc port 8554 using media_kit | `test_bug_001_rtsp_url_construction` | Verified |

---

## 8. Pre-Fix Checklist

Copy and paste this checklist before starting any bug fix session:

```
## Pre-Fix Checklist — BUG-<ID>

### 1. Reproduce
- [ ] Bug documented in Bug Registry with ID
- [ ] Reproduction steps recorded
- [ ] Error output captured (logcat / traceback / curl response)
- [ ] Environment noted (server IP, camera, device ID)

### 2. Baseline
- [ ] `cd frigate-intelligence && python -m pytest tests/ -v` — passes (record count: ___)
- [ ] `cd frigate_app && flutter test` — passes
- [ ] `cd frigate_app && flutter analyze` — zero issues

### 3. Investigate
- [ ] Root cause identified (not just symptom)
- [ ] Affected files identified
- [ ] No unrelated changes planned

### 4. Fix
- [ ] Minimal change applied to root cause
- [ ] No new dependencies added (or justified if added)
- [ ] Logging added for error paths (no silent failures)
- [ ] Existing architecture preserved (Clean Architecture layers)

### 5. Regression Test
- [ ] Test written that fails without the fix
- [ ] Test passes with the fix
- [ ] Test follows naming convention: `test_bug_<ID>_<description>`

### 6. Verify
- [ ] `python -m pytest tests/ -v` — all pass, count ≥ baseline
- [ ] `flutter test` — all pass
- [ ] `flutter analyze` — zero issues
- [ ] `flutter build apk --debug` — succeeds
- [ ] Bug Registry updated with fix details and status

### 7. Deploy (if applicable)
- [ ] Deployment Checklist (Section 6) completed
- [ ] Change tested on target device (R5CY23R9DXR)
- [ ] Change tested against live Frigate server (192.168.85.203:5000)
```

---

## Quick Reference

### Project Structure

```
YOLO/
├── frigate-intelligence/          # Python backend (FastAPI + SQLite)
│   ├── src/frigate_intelligence/
│   │   ├── domain/                # Entities (QueryResult, etc.)
│   │   ├── use_cases/             # Business logic (TextToSQL, Analytics, POS)
│   │   ├── interface_adapters/    # Controllers, presenters
│   │   ├── infrastructure/        # FastAPI app, SQLite gateway, Frigate client
│   │   └── config/                # Dependency injection container
│   ├── tests/
│   │   ├── unit/                  # Unit tests (use cases, domain, adapters)
│   │   ├── integration/           # Integration tests (API, SQLite gateway)
│   │   └── e2e/                   # End-to-end tests
│   └── pyproject.toml             # Python project config (pytest, ruff)
├── frigate_app/                   # Flutter mobile app (Riverpod)
│   ├── lib/
│   │   ├── presentation/
│   │   │   ├── pages/             # main_scaffold, chat_page, live_view_tab, playback_tab
│   │   │   ├── providers/         # live_stream_provider, recording_provider, server_config
│   │   │   └── widgets/           # chat_bubble, full_screen_gallery, timeline_widget
│   │   ├── data/                  # API client, models
│   │   └── main.dart
│   ├── test/                      # Flutter widget tests
│   ├── android/                   # Android build config (compileSdk 36, minSdk 24)
│   └── pubspec.yaml               # Flutter dependencies
├── frigate-config.yml             # Frigate server config (go2rtc, cameras, detection)
├── frigate-docker-compose.yml     # Frigate Docker Compose
└── Phase10_Flutter_NVR_App.md     # Phase 10 roadmap & implementation notes
```

### Key Server Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| Frigate Web UI | `http://192.168.85.203:5000` | Frigate frontend + API |
| Frigate API | `http://192.168.85.203:5000/api/` | REST API |
| go2rtc streams | `http://192.168.85.203:5000/api/go2rtc/streams` | Stream management |
| RTSP restream | `rtsp://192.168.85.203:8554/{camera}` | Live streaming |
| VOD clips | `http://192.168.85.203:5000/api/{cam}/start/{ts}/end/{ts}/clip.mp4` | Playback |
| Backend API | `http://192.168.85.203:8088` | AI intelligence service |
| Web Panel | `http://192.168.85.203:3000` | Next.js web dashboard |

### Key Commands

```bash
# Backend
cd frigate-intelligence
python -m pytest tests/ -v --tb=short          # Run tests
ruff check src/ tests/                           # Lint

# Frontend
cd frigate_app
flutter test                                     # Run tests
flutter analyze                                  # Static analysis
flutter build apk --debug                        # Build

# Device
adb -s R5CY23R9DXR logcat -s flutter:I          # Capture logs
adb -s R5CY23R9DXR install -r build/app/outputs/flutter-apk/app-debug.apk  # Install

# Server
curl -s http://192.168.85.203:5000/api/go2rtc/streams | python -m json.tool  # Check streams
curl -s http://192.168.85.203:8088/health                                     # Health check
```
