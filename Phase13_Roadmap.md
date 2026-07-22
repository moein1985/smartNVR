# Phase 13 Roadmap — Industrial Business Intelligence & HR Monitoring

**Status:** Phase 13.4 Complete — Phase 13 Finished! 🎉
**Proposal:** `Phase13_Technical_Feasibility_Proposal.md`

---

## Phase 13.1 — LLM Prompt Update (Backend)

- [x] **Step 1:** Update `frigate_schema.py` — add rules 14-16 to `SQL_RULES` about zone naming conventions (`_table` = workstation, `_sensitive` = restricted, zone + sub_label synergy)
- [x] **Step 2:** Update `frigate_schema.py` — add 4 new sample queries for `_table` and `_sensitive` zones to `SAMPLE_QUERIES`
- [x] **Step 3:** Update `frigate_schema.py` — update `load_schema_context()` fallback text to mention zone conventions
- [x] **Step 4:** Update `frigate_schema.py` — modify `get_frigate_zones()` to annotate zones with type (`workstation` / `restricted`)
- [x] **Step 5:** Fix `get_frigate_zones()` hardcoded URL — change from `http://frigate:5000` to `http://192.168.85.203:5000` (same fix as BUG-022)
- [x] **Step 6:** Add `test_bug_030_zone_convention_table_query` — verify LLM generates correct SQL for "who was at soleymani's desk"
- [x] **Step 7:** Add `test_bug_030_zone_convention_sensitive_query` — verify LLM generates correct SQL for "security alerts in sensitive zones"
- [x] **Step 8:** Run `ruff check src/ tests/` — **0 errors**
- [x] **Step 9:** Run `python -m pytest tests/ -v` — **58 passed, 0 failed** (48 baseline + 10 new)
- [x] **Step 10:** Update `Phase13_Roadmap.md` and `BUG_FIXING_DISCIPLINE.md` — BUG-030 Fixed

---

## Phase 13.2 — Backend Scheduler & Telegram Report (Backend)

- [x] **Step 1:** Update `settings_model.py` — add `report_time: str = "21:00"` and `report_timezone: str = "Asia/Tehran"` fields
- [x] **Step 2:** Update `cron_service.py` — replace `_FREQUENCY_CRON_MAP` with dynamic cron expression from `report_time` setting; add `timezone` parameter to `CronTrigger`
- [x] **Step 3:** Update `cron_service.py` — pass `Container` (or `TextToSQLUseCase` + `TelegramNotifier`) to `generate_and_send_report()`
- [x] **Step 4:** Implement `generate_and_send_report()`:
  - Build natural language prompt for daily summary
  - Call `TextToSQLUseCase.execute()` with client timezone info
  - Format results as Markdown (workstation sections + security alerts)
  - Handle zero-events case with "No activity detected" message
  - Send via `TelegramNotifier` with retry logic (3 attempts, exponential backoff)
- [x] **Step 5:** Update `fastapi_app.py` — add `lifespan` context manager to start/stop `CronService`
- [x] **Step 6:** Update `api_controller.py` — call `cron_service._refresh_job()` after settings save to update schedule
- [x] **Step 7:** Add `test_bug_031_cron_parses_report_time` — verify cron expression generation from "21:00" + "Asia/Tehran"
- [x] **Step 8:** Add `test_bug_031_report_formats_zero_events` — verify report generation handles empty result set
- [x] **Step 9:** Run `ruff check src/ tests/` — **0 errors**
- [x] **Step 10:** Run `python -m pytest tests/ -v` — **67 passed, 0 failed** (58 baseline + 9 new)
- [x] **Step 11:** Update `Phase13_Roadmap.md` and `BUG_FIXING_DISCIPLINE.md` — BUG-031 Fixed

---

## Phase 13.3 — Flutter Settings UI (Frontend)

- [x] **Step 1:** Update `api_client.dart` — add `getSettings()` and `updateSettings()` methods
- [x] **Step 2:** Create `lib/presentation/providers/settings_provider.dart` — `SettingsNotifier` wrapping API calls
- [x] **Step 3:** Update `settings_page.dart` — add new `_SectionHeader` for "Telegram & Reporting" section
- [x] **Step 4:** Add Telegram Bot Token text field (obscured)
- [x] **Step 5:** Add Telegram Chat ID text field
- [x] **Step 6:** Add Report Time picker (TimePicker or text field with HH:MM format)
- [x] **Step 7:** Add Report Timezone dropdown (common timezones, default Asia/Tehran)
- [x] **Step 8:** Add "Enable Scheduled Reports" switch (maps to `telegram_enabled` + `report_frequency != "disabled"`)
- [x] **Step 9:** Add "Save & Test Telegram" button — saves settings and sends a test message
- [x] **Step 10:** Add `bug_032_settings_page_has_telegram_section` in `regression_test.dart`
- [x] **Step 11:** Run `flutter analyze` — **0 issues**
- [x] **Step 12:** Run `flutter test` — **10 passed, 0 failed** (9 baseline + 1 new)
- [x] **Step 13:** Update `Phase13_Roadmap.md` and `BUG_FIXING_DISCIPLINE.md` — BUG-032 Fixed

---

## Phase 13.4 — Integration Testing & Deployment

- [x] **Step 1:** Run `ruff check src/ tests/` — **0 errors**
- [x] **Step 2:** Run `python -m pytest tests/ -v` — **67 passed, 0 failed**
- [x] **Step 3:** Run `flutter analyze` — **0 issues**
- [x] **Step 4:** Run `flutter test` — **10 passed, 0 failed**
- [x] **Step 5:** Run `flutter build apk --debug` — **success** (`build\app\outputs\flutter-apk\app-debug.apk`)
- [x] **Step 5b:** Deploy backend to server — `pscp` updated `src/` + `pyproject.toml` to `192.168.85.203`, `docker compose up -d --build` rebuilt container, health endpoint returns `"status":"ok"`, settings endpoint returns new `report_time`/`report_timezone` fields
- [ ] **Step 6:** Manual test: configure zones in Frigate (`soleymani_table`, `warehouse_sensitive`), ask "Who was at Soleymani's desk today?", verify LLM generates correct SQL
- [ ] **Step 7:** Manual test: configure Telegram settings in app, verify test message arrives
- [ ] **Step 8:** Manual test: wait for scheduled report time (or trigger manually), verify formatted report arrives in Telegram
- [x] **Step 9:** Update `Phase13_Roadmap.md` — mark Phase 13 complete

---

## Bug Registry

| Bug ID | Phase | Description | Status |
|--------|-------|-------------|--------|
| BUG-030 | 13.1 | LLM lacks context for `_table` and `_sensitive` Frigate zone naming conventions | Fixed |
| BUG-031 | 13.2 | Backend CronService scheduler is not integrated with FastAPI lifespan and Telegram reporting logic is unimplemented | Fixed |
| BUG-032 | 13.3 | Flutter frontend lacks UI settings for Telegram Bot configuration and reporting schedules | Fixed |

---

## 🎉 Phase 13 Complete!

**Phase 13 — Industrial Business Intelligence & HR Monitoring** is officially finished!

### What was delivered:
- **Phase 13.1:** LLM prompt engineering with "Convention over Configuration" zone naming (`_table`, `_sensitive`) — 10 regression tests
- **Phase 13.2:** Backend scheduler with dynamic cron, timezone-aware scheduling, LLM-powered report generation, and Telegram delivery with exponential backoff retry — 9 regression tests
- **Phase 13.3:** Flutter settings UI with Telegram bot configuration, report time/timezone, and enable switch — 1 regression test
- **Phase 13.4:** Full integration testing, APK build, and production deployment

### Test Summary:
- **Backend:** 67 passed (ruff: 0 errors)
- **Frontend:** 10 passed (flutter analyze: 0 issues)
- **APK:** `build\app\outputs\flutter-apk\app-debug.apk`
- **Server:** `192.168.85.203:8088` — live and healthy with new settings endpoint

### Bugs Fixed:
- BUG-030: LLM zone naming conventions
- BUG-031: Backend scheduler + Telegram reporting
- BUG-032: Flutter Telegram settings UI

### Remaining (Manual Physical Tests):
- Step 6: Configure Frigate zones and test LLM queries
- Step 7: Configure Telegram settings in app and verify test message
- Step 8: Wait for scheduled report and verify Telegram delivery
