# Phase 13 — Technical Feasibility Proposal
## Industrial Business Intelligence & HR Monitoring via Zone Conventions

**Date:** 2026-07-22  
**Status:** Proposal — Pending Review  
**Author:** Cascade (AI Pair Programmer)

---

## 1. Executive Summary

Phase 13 transforms the Frigate Intelligence platform from a pure NVR analytics tool into an **Industrial Business Intelligence & HR monitoring system** by leveraging a "Convention over Configuration" approach to Frigate zone naming. Instead of building complex database schemas or admin panels for zone semantics, the system will infer zone purpose from naming suffixes (`_table`, `_sensitive`) and combine this with CompreFace face recognition (`sub_label`) to answer business questions like "Who was at Soleymani's desk today?" and "Was there unauthorized access to the warehouse?"

A nightly scheduler will automatically generate a formatted daily summary and deliver it via Telegram Bot, requiring zero user interaction.

---

## 2. Current Architecture Inventory

Before evaluating feasibility, here is what already exists in the codebase:

### 2.1 Backend (`frigate-intelligence/`)

| Component | File | Status |
|-----------|------|--------|
| **LLM Prompt Builder** | `src/.../use_cases/text_to_sql/prompt_builder.py` | Builds system prompt with schema, sample queries, SQL rules, and time context |
| **Frigate Schema** | `src/.../interface_adapters/schemas/frigate_schema.py` | 13 SQL rules, 15 sample queries, `get_frigate_zones()` fetches zone names from Frigate API |
| **Settings Model** | `src/.../domain/models/settings_model.py` | Already has `telegram_enabled`, `telegram_bot_token`, `telegram_chat_id`, `report_frequency`, `report_target` fields |
| **Settings Persistence** | `src/.../infrastructure/config/settings_manager.py` | JSON file (`settings.json`) — load/save via `SettingsManager` |
| **Cron Scheduler** | `src/.../infrastructure/scheduler/cron_service.py` | `AsyncIOScheduler` (APScheduler) with `_FREQUENCY_CRON_MAP` — **skeleton only**, `generate_and_send_report()` is a stub |
| **Telegram Notifier** | `src/.../infrastructure/notifiers/telegram_notifier.py` | Working `TelegramNotifier` class using `python-telegram-bot` Bot API |
| **Notification Use Case** | `src/.../use_cases/send_notification/send_notification_use_case.py` | `SendNotificationUseCase` wraps notifier with async event loop |
| **FastAPI App** | `src/.../infrastructure/api/fastapi_app.py` | `create_app()` — does NOT start CronService currently |
| **API Controller** | `src/.../interface_adapters/controllers/api_controller.py` | Has `GET /settings` and `POST /settings` endpoints |
| **Intent Classification** | `src/.../use_cases/text_to_sql/text_to_sql_use_case.py` | `smart_query()` returns `intent` (`event_query` / `playback_query`) |

### 2.2 Frontend (`frigate_app/`)

| Component | File | Status |
|-----------|------|--------|
| **Settings Page** | `lib/presentation/pages/settings_page.dart` | Server IP/port config + mock mode toggle. No Telegram settings UI. |
| **API Client** | `lib/data/datasources/api_client.dart` | Has `query()`, `health()`. No `getSettings()` / `updateSettings()` calls. |
| **Navigation** | `lib/presentation/providers/navigation_provider.dart` | Riverpod-based tab switching (Phase 12.5) |

### 2.3 Key Observations

1. **The infrastructure is 70% ready.** Settings model already has Telegram fields. CronService skeleton exists. TelegramNotifier is functional. The missing pieces are: (a) wiring the scheduler into the FastAPI startup, (b) implementing the report generation logic, (c) teaching the LLM about zone conventions, (d) Flutter settings UI for Telegram config.

2. **Settings are persisted as JSON** (`settings.json`), not in SQLite. This is appropriate — settings are key-value configuration, not transactional data. No need to add a SQLite settings table.

3. **The CronService is not started.** `fastapi_app.py`'s `create_app()` does not instantiate or start `CronService`. It needs to be injected as a lifespan event.

---

## 3. Feasibility Assessment

### 3.1 Backend Scheduler (APScheduler)

**Verdict: Fully feasible — infrastructure already exists.**

The `CronService` at `cron_service.py` already uses `AsyncIOScheduler` from APScheduler, which integrates natively with FastAPI's async event loop. The `_FREQUENCY_CRON_MAP` currently has fixed presets (`daily_8am`, `daily_8pm`, `weekly`).

**Required changes:**
- Replace fixed `_FREQUENCY_CRON_MAP` with a configurable cron expression derived from a `report_time` setting (e.g., `"21:00"` → `"0 21 * * *"`).
- Start `CronService` in FastAPI's lifespan context (using `@asynccontextmanager`).
- Implement the `generate_and_send_report()` function to:
  1. Load settings (Telegram token, chat ID, report time)
  2. Construct a natural language prompt like "Summarize today's events for all `_table` and `_sensitive` zones"
  3. Call `TextToSQLUseCase.execute()` to query the database
  4. Format the results as a Markdown summary
  5. Send via `TelegramNotifier`

**Timezone consideration:** The server runs in UTC. The `report_time` setting should be interpreted in the client's timezone. We should add a `report_timezone` field to `SettingsModel` (default: `"Asia/Tehran"`). The scheduler should use `APScheduler`'s `timezone` parameter on the `CronTrigger` to ensure the job fires at the correct local time.

### 3.2 Telegram Integration

**Verdict: Fully feasible — `TelegramNotifier` is already implemented.**

The `TelegramNotifier` class uses `python-telegram-bot`'s `Bot.send_message()` with Markdown parsing. The `SendNotificationUseCase` wraps it with async event loop handling.

**Required changes:**
- The `generate_and_send_report()` function needs access to both `TextToSQLUseCase` (for querying) and `TelegramNotifier` (for sending). Currently it only receives `SettingsManager`. We need to pass the full `Container` or specific use cases.
- Add a `report_timezone` field to `SettingsModel`.
- Add a `report_time` field (string, format `"HH:MM"`, default `"21:00"`).

### 3.3 Settings Persistence

**Verdict: JSON file is the correct approach — no SQLite needed.**

The existing `SettingsManager` persists to `settings.json`. This is appropriate for configuration data that:
- Is read infrequently (on startup, on settings update)
- Has no relational queries
- Needs to survive container restarts

**Required additions to `SettingsModel`:**
```python
class SettingsModel(BaseModel):
    # ... existing fields ...
    report_time: str = "21:00"          # HH:MM format, client local time
    report_timezone: str = "Asia/Tehran" # IANA timezone name
```

### 3.4 LLM Prompt Engineering

**Verdict: Feasible with careful rule design — risk of confusing the model is low if rules are concise.**

The current `SQL_RULES` string has 13 rules. Adding 2-3 more rules about zone conventions is well within the `gemini-2.5-flash` context window and attention budget.

**Risk assessment:** The `gemini-2.5-flash` model handles 13 rules well (verified in Phase 12.3). Adding rules 14-16 about zone conventions should not degrade performance, provided they are:
- Concise (one paragraph each, not verbose)
- Use concrete examples
- Don't contradict existing rules

---

## 4. Prompt Engineering Strategy

### 4.1 New SQL Rules (to be appended to `SQL_RULES` in `frigate_schema.py`)

```
14. Zone Naming Convention: Zones ending with `_table` (e.g., `soleymani_table`) represent employee workstations. Zones ending with `_sensitive` (e.g., `warehouse_sensitive`) represent secure/restricted areas. When a user asks about "desk presence", "work hours", or "who was at X's desk", filter zones LIKE '%_table'. When asking about "unauthorized access", "security alerts", or "restricted areas", filter zones LIKE '%_sensitive'.

15. Zone + sub_label Synergy: To find "who was at Soleymani's desk", combine zone and sub_label: WHERE zones LIKE '%soleymani_table%' AND sub_label NOT LIKE '%soleymani%' AND label='person'. This identifies anyone OTHER than Soleymani at their desk. To find Soleymani's active hours: WHERE zones LIKE '%soleymani_table%' AND sub_label LIKE '%soleymani%'.

16. Work Hours Calculation: To calculate active desk time for an employee, query events in their `_table` zone with their `sub_label`, then compute SUM(end_time - start_time) for overlapping or consecutive events. Use MIN(start_time) as first_seen and MAX(end_time) as last_seen for daily presence summary.
```

### 4.2 New Sample Queries (to be appended to `SAMPLE_QUERIES`)

```sql
-- Who was at Soleymani's desk today (excluding Soleymani)?
SELECT id, sub_label, datetime(start_time, 'unixepoch', 'localtime') as start_time,
       datetime(end_time, 'unixepoch', 'localtime') as end_time
FROM event
WHERE zones LIKE '%soleymani_table%' AND label='person'
  AND sub_label NOT LIKE '%soleymani%'
  AND start_time >= strftime('%s', 'now', 'start of day')
ORDER BY start_time DESC;

-- Soleymani's work hours today (first seen, last seen, total duration)
SELECT sub_label,
       datetime(MIN(start_time), 'unixepoch', 'localtime') as first_seen,
       datetime(MAX(end_time), 'unixepoch', 'localtime') as last_seen,
       ROUND(SUM(end_time - start_time) / 60, 1) as total_minutes
FROM event
WHERE zones LIKE '%soleymani_table%' AND sub_label LIKE '%soleymani%'
  AND start_time >= strftime('%s', 'now', 'start of day')
GROUP BY sub_label;

-- Security alerts for sensitive zones today
SELECT id, camera, zones, sub_label,
       datetime(start_time, 'unixepoch', 'localtime') as start_time
FROM event
WHERE zones LIKE '%_sensitive%' AND label='person'
  AND start_time >= strftime('%s', 'now', 'start of day')
ORDER BY start_time DESC;

-- Daily summary: all _table zone activity grouped by person
SELECT sub_label, zones,
       datetime(MIN(start_time), 'unixepoch', 'localtime') as first_seen,
       datetime(MAX(end_time), 'unixepoch', 'localtime') as last_seen,
       COUNT(*) as event_count
FROM event
WHERE zones LIKE '%_table%' AND label='person' AND sub_label IS NOT NULL
  AND start_time >= strftime('%s', 'now', 'start of day')
GROUP BY sub_label, zones
ORDER BY zones, first_seen;
```

### 4.3 Schema Description Update

Update the fallback schema text in `load_schema_context()` to mention zone conventions:

```python
Zones: configured via Frigate UI. Zone naming convention:
- [name]_table: employee workstation (e.g., soleymani_table)
- [name]_sensitive: secure/restricted area (e.g., warehouse_sensitive)
```

Also update `get_frigate_zones()` to annotate zones with their type:

```python
def get_frigate_zones(frigate_url: str = "http://192.168.85.203:5000") -> str:
    # ... fetch zones ...
    annotated = []
    for zone_name, cam_name in zones:
        if zone_name.endswith("_table"):
            annotated.append(f"{zone_name} (camera: {cam_name}, type: workstation)")
        elif zone_name.endswith("_sensitive"):
            annotated.append(f"{zone_name} (camera: {cam_name}, type: restricted)")
        else:
            annotated.append(f"{zone_name} (camera: {cam_name})")
    return "Available zones: " + ", ".join(annotated)
```

### 4.4 Why This Won't Confuse the Model

1. **Rules are additive, not contradictory** — rules 14-16 introduce new semantic context without modifying rules 1-13.
2. **Examples are concrete** — using `soleymani_table` and `warehouse_sensitive` as examples grounds the abstraction.
3. **The model already understands `sub_label`** — rule 13 established this in Phase 12.3. Rules 14-16 simply combine it with `zones`.
4. **`gemini-2.5-flash` has a 1M token context window** — 16 rules + 19 sample queries is trivially small.

---

## 5. Architectural Recommendations

### 5.1 Edge Cases & Robustness

| Edge Case | Recommendation |
|-----------|----------------|
| **Days with zero events** | The report should still be sent, stating "No activity detected today." This is important — silence is worse than an empty report. |
| **Timezone for scheduler** | Add `report_timezone` to `SettingsModel` (default: `"Asia/Tehran"`). Pass this to `CronTrigger` via `timezone=pytz.timezone(settings.report_timezone)`. |
| **Telegram API failure** | Wrap `TelegramNotifier.send()` in try/except with logging. Retry up to 3 times with exponential backoff. If all retries fail, log the error and skip — don't crash the scheduler. |
| **LLM API failure during report generation** | If `smart_query()` or `execute()` fails, fall back to a raw SQL query (no LLM) that selects all events for the day grouped by zone type. Format as a simple table. |
| **Multiple `_table` zones** | The report should iterate over all zones ending in `_table` and generate a per-employee section. Don't hardcode `soleymani_table`. |
| **Container restart** | `settings.json` persists across restarts. The scheduler re-reads settings on startup via `_refresh_job()`. No data loss. |
| **Concurrent settings update while scheduler is running** | Call `cron_service._refresh_job()` after `POST /settings` saves new settings. This re-creates the cron job with the new schedule. |
| **Zone name changes in Frigate** | Since zones are fetched dynamically from the Frigate API at prompt build time, zone name changes are picked up automatically on the next query. No restart needed. |

### 5.2 Report Format (Telegram Markdown)

```
📊 Daily Security & HR Report — 2026-07-22

🏢 Workstation Activity:
━━━━━━━━━━━━━━━━━━━━━━━
👤 Soleymani (soleymani_table):
   First seen: 08:32 | Last seen: 17:45 | Active: ~8.2h
   ⚠️ 3 visits by unknown persons at desk

👤 Moein (moein_table):
   First seen: 09:15 | Last seen: 18:00 | Active: ~7.5h

🔒 Restricted Area Alerts:
━━━━━━━━━━━━━━━━━━━━━━━
⚠️ warehouse_sensitive: 2 events
   14:22 — unknown person detected
   19:05 — moein detected

📈 Summary: 2 employees tracked, 5 security alerts, 0 unknown visitors at workstations.
```

### 5.3 Report Generation Flow

```
CronService (21:00 Asia/Tehran)
  → generate_and_send_report()
    → Load settings (Telegram token, chat_id, timezone)
    → Build LLM prompt: "Summarize today's events for all _table and _sensitive zones"
    → TextToSQLUseCase.execute()
    → Format QueryResponse rows as Markdown
    → TelegramNotifier.send(message)
    → Log success/failure
```

### 5.4 FastAPI Lifespan Integration

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    cron = CronService(settings_manager=SettingsManager(), container=container)
    cron.start()
    app.state.cron = cron
    yield
    # Shutdown
    cron.stop()

app = FastAPI(..., lifespan=lifespan)
```

---

## 6. Actionable Roadmap

### Phase 13.1 — LLM Prompt Update (Backend)

**Goal:** Teach the LLM about `_table` and `_sensitive` zone conventions.

- [ ] **Step 1:** Update `frigate_schema.py` — add rules 14-16 to `SQL_RULES` about zone naming conventions
- [ ] **Step 2:** Update `frigate_schema.py` — add 4 new sample queries for `_table` and `_sensitive` zones to `SAMPLE_QUERIES`
- [ ] **Step 3:** Update `frigate_schema.py` — update `load_schema_context()` fallback text to mention zone conventions
- [ ] **Step 4:** Update `frigate_schema.py` — modify `get_frigate_zones()` to annotate zones with type (`workstation` / `restricted`)
- [ ] **Step 5:** Fix `get_frigate_zones()` hardcoded URL — change from `http://frigate:5000` to `http://192.168.85.203:5000` (same fix as BUG-022)
- [ ] **Step 6:** Add `test_bug_030_zone_convention_table_query` — verify LLM generates correct SQL for "who was at soleymani's desk"
- [ ] **Step 7:** Add `test_bug_030_zone_convention_sensitive_query` — verify LLM generates correct SQL for "security alerts in sensitive zones"
- [ ] **Step 8:** Run `ruff check src/ tests/` — 0 errors
- [ ] **Step 9:** Run `python -m pytest tests/ -v` — all pass
- [ ] **Step 10:** Update `Phase13_Roadmap.md` and `BUG_FIXING_DISCIPLINE.md` — BUG-030 Fixed

### Phase 13.2 — Backend Scheduler & Telegram Report (Backend)

**Goal:** Implement the nightly automated report generation and Telegram delivery.

- [ ] **Step 1:** Update `settings_model.py` — add `report_time: str = "21:00"` and `report_timezone: str = "Asia/Tehran"` fields
- [ ] **Step 2:** Update `cron_service.py` — replace `_FREQUENCY_CRON_MAP` with dynamic cron expression from `report_time` setting; add `timezone` parameter to `CronTrigger`
- [ ] **Step 3:** Update `cron_service.py` — pass `Container` (or `TextToSQLUseCase` + `TelegramNotifier`) to `generate_and_send_report()`
- [ ] **Step 4:** Implement `generate_and_send_report()`:
  - Build natural language prompt for daily summary
  - Call `TextToSQLUseCase.execute()` with client timezone info
  - Format results as Markdown (workstation sections + security alerts)
  - Handle zero-events case with "No activity detected" message
  - Send via `TelegramNotifier` with retry logic (3 attempts, exponential backoff)
- [ ] **Step 5:** Update `fastapi_app.py` — add `lifespan` context manager to start/stop `CronService`
- [ ] **Step 6:** Update `api_controller.py` — call `cron_service._refresh_job()` after settings save to update schedule
- [ ] **Step 7:** Add `test_bug_031_cron_parses_report_time` — verify cron expression generation from "21:00" + "Asia/Tehran"
- [ ] **Step 8:** Add `test_bug_031_report_formats_zero_events` — verify report generation handles empty result set
- [ ] **Step 9:** Run `ruff check src/ tests/` — 0 errors
- [ ] **Step 10:** Run `python -m pytest tests/ -v` — all pass
- [ ] **Step 11:** Update `Phase13_Roadmap.md` and `BUG_FIXING_DISCIPLINE.md` — BUG-031 Fixed

### Phase 13.3 — Flutter Settings UI (Frontend)

**Goal:** Add Telegram configuration and reporting schedule settings to the Flutter app.

- [ ] **Step 1:** Update `api_client.dart` — add `getSettings()` and `updateSettings()` methods
- [ ] **Step 2:** Create `lib/presentation/providers/settings_provider.dart` — `SettingsNotifier` wrapping API calls
- [ ] **Step 3:** Update `settings_page.dart` — add new `_SectionHeader` for "Telegram & Reporting" section
- [ ] **Step 4:** Add Telegram Bot Token text field (obscured)
- [ ] **Step 5:** Add Telegram Chat ID text field
- [ ] **Step 6:** Add Report Time picker (TimePicker or text field with HH:MM format)
- [ ] **Step 7:** Add Report Timezone dropdown (common timezones, default Asia/Tehran)
- [ ] **Step 8:** Add "Enable Scheduled Reports" switch (maps to `telegram_enabled` + `report_frequency != "disabled"`)
- [ ] **Step 9:** Add "Save & Test Telegram" button — saves settings and sends a test message
- [ ] **Step 10:** Add `bug_032_settings_page_has_telegram_section` in `regression_test.dart`
- [ ] **Step 11:** Run `flutter analyze` — 0 issues
- [ ] **Step 12:** Run `flutter test` — all pass
- [ ] **Step 13:** Update `Phase13_Roadmap.md` and `BUG_FIXING_DISCIPLINE.md` — BUG-032 Fixed

### Phase 13.4 — Integration Testing & Deployment

**Goal:** End-to-end verification and APK build.

- [ ] **Step 1:** Run `ruff check src/ tests/` — 0 errors
- [ ] **Step 2:** Run `python -m pytest tests/ -v` — all pass
- [ ] **Step 3:** Run `flutter analyze` — 0 issues
- [ ] **Step 4:** Run `flutter test` — all pass
- [ ] **Step 5:** Run `flutter build apk --debug` — success
- [ ] **Step 6:** Manual test: configure zones in Frigate (`soleymani_table`, `warehouse_sensitive`), ask "Who was at Soleymani's desk today?", verify LLM generates correct SQL
- [ ] **Step 7:** Manual test: configure Telegram settings in app, verify test message arrives
- [ ] **Step 8:** Manual test: wait for scheduled report time (or trigger manually), verify formatted report arrives in Telegram
- [ ] **Step 9:** Update `Phase13_Roadmap.md` — mark Phase 13 complete

---

## 7. Dependency Analysis

### 7.1 New Python Packages Required

| Package | Purpose | Already in `pyproject.toml`? |
|---------|---------|------------------------------|
| `apscheduler` | Cron scheduler | ✅ Yes (already used in `cron_service.py`) |
| `python-telegram-bot` | Telegram Bot API | ✅ Yes (already used in `telegram_notifier.py`) |
| `pytz` | Timezone handling for scheduler | ❓ Need to verify — may need to add |

### 7.2 New Flutter Packages Required

None. All UI components (TextFormField, SwitchListTile, TimePicker) are available in the standard Flutter SDK.

### 7.3 File Change Summary

| File | Phase | Change Type |
|------|-------|-------------|
| `frigate-intelligence/src/.../schemas/frigate_schema.py` | 13.1 | Modify — add rules, queries, zone annotations |
| `frigate-intelligence/src/.../models/settings_model.py` | 13.2 | Modify — add `report_time`, `report_timezone` |
| `frigate-intelligence/src/.../scheduler/cron_service.py` | 13.2 | Modify — implement report generation, dynamic cron |
| `frigate-intelligence/src/.../api/fastapi_app.py` | 13.2 | Modify — add lifespan for CronService |
| `frigate-intelligence/src/.../controllers/api_controller.py` | 13.2 | Modify — refresh cron job on settings save |
| `frigate-intelligence/tests/integration/test_api.py` | 13.1, 13.2 | Add — new test cases |
| `frigate_app/lib/data/datasources/api_client.dart` | 13.3 | Modify — add settings API methods |
| `frigate_app/lib/presentation/providers/settings_provider.dart` | 13.3 | **New file** |
| `frigate_app/lib/presentation/pages/settings_page.dart` | 13.3 | Modify — add Telegram section |
| `frigate_app/test/regression_test.dart` | 13.3 | Add — new test case |

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM misinterprets zone conventions | Low | Medium | Comprehensive sample queries + rules; regression tests verify SQL output |
| Telegram API rate limiting | Low | Low | Retry with backoff; single message per day is well within limits |
| Scheduler doesn't fire in Docker | Medium | High | Use `AsyncIOScheduler` (already in codebase); verify with manual trigger test |
| Timezone mismatch (server UTC vs client +03:30) | Medium | Medium | `report_timezone` setting + `pytz` on `CronTrigger`; same approach as Phase 12.1 time sync |
| Zero events day produces empty report | Low | Low | Explicit "No activity detected" fallback message |
| Frigate zone names don't follow convention | Medium | Low | Rules use `LIKE '%_table%'` which is forgiving; if no zones match, report states "No workstation zones configured" |

---

## 9. Conclusion

Phase 13 is **highly feasible** with minimal new infrastructure. The codebase already contains 70% of the required components (CronService skeleton, TelegramNotifier, SettingsModel with Telegram fields, SettingsManager JSON persistence). The remaining 30% is:

1. **Prompt engineering** (2-3 new SQL rules + 4 sample queries) — low risk, additive
2. **Report generation logic** (implementing the stub `generate_and_send_report()`) — medium effort, straightforward
3. **FastAPI lifespan integration** (start/stop scheduler) — small change, well-documented pattern
4. **Flutter settings UI** (new section in existing page) — medium effort, no new dependencies

The "Convention over Configuration" approach is elegant — it requires zero database schema changes, zero admin panels, and zero complex configuration. The LLM simply needs to be taught the naming convention, and the Frigate UI handles zone definition. This is the most maintainable path to industrial BI functionality.

**Estimated effort:** 3-4 coding sessions (one per sub-phase).  
**Estimated bug count:** 3 (BUG-030, BUG-031, BUG-032).  
**Recommended execution order:** 13.1 → 13.2 → 13.3 → 13.4 (backend first, frontend last).
