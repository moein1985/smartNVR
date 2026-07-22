# Phase 13 Roadmap — Industrial Business Intelligence & HR Monitoring

**Status:** Phase 13.1 Complete — Phase 13.2 Next
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

---

## Phase 13.3 — Flutter Settings UI (Frontend)

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

---

## Phase 13.4 — Integration Testing & Deployment

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

## Bug Registry

| Bug ID | Phase | Description | Status |
|--------|-------|-------------|--------|
| BUG-030 | 13.1 | LLM lacks context for `_table` and `_sensitive` Frigate zone naming conventions | Fixed |
| BUG-031 | 13.2 | Backend CronService scheduler is not integrated with FastAPI lifespan and Telegram reporting logic is unimplemented | Open |
| BUG-032 | 13.3 | Flutter frontend lacks UI settings for Telegram Bot configuration and reporting schedules | Open |
