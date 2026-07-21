# Phase 12 — Execution Roadmap

**Source of truth for tracking Phase 12 implementation progress.**  
**Extracted from `Phase12_Technical_Feasibility_Proposal.md` Section 4.**

---

## Phase 12.1 — Time Synchronization Foundation (Backend)

- [x] **Step 1:** Update `api_models.py` — add `server_timestamp`, `server_timezone`, `server_datetime_iso` to `HealthResponse`; add `client_timezone`, `client_offset_minutes`, `client_timestamp` to `QueryRequest`
- [x] **Step 2:** Update `api_controller.py` — `health()` returns current UTC datetime details
- [x] **Step 3:** Update `prompt_context.py` — add `time_context` field, include in `as_system_prompt()`
- [x] **Step 4:** Update `prompt_builder.py` — accept `client_tz_info` dict, compute absolute time references, inject into prompt
- [x] **Step 5:** Update `text_to_sql_use_case.py` — accept client timezone params in `execute()` and `execute_streaming()`, pass to prompt builder
- [x] **Step 6:** Update `api_controller.py` `query()` — pass client TZ fields from `QueryRequest` to `TextToSQLRequest`
- [x] **Step 7:** Add `test_bug_023_health_endpoint_returns_timestamp` in `tests/integration/test_api.py`
- [x] **Step 8:** Add `test_bug_023_query_accepts_client_timezone` in `tests/integration/test_api.py`
- [x] **Step 9:** Run `ruff check src/ tests/` — 0 errors
- [x] **Step 10:** Run `python -m pytest tests/ -v` — 43 passed, 1 pre-existing failure (unrelated)
- [x] **Step 11:** Update `Phase12_Roadmap.md` — check off completed steps
- [x] **Step 12:** Update `BUG_FIXING_DISCIPLINE.md` — record BUG-023 as Fixed

---

## Phase 12.2 — Time Synchronization UI (Flutter Frontend)

- [x] **Step 1:** Created `lib/presentation/providers/time_sync_provider.dart` — `TimeSyncNotifier` with periodic health check, skew calculation, `hasSignificantSkew` getter (>2 min threshold)
- [x] **Step 2:** Updated `lib/data/datasources/api_client.dart` — `query()` includes `client_timezone`, `client_offset_minutes`, `client_timestamp` in POST body
- [x] **Step 3:** Updated `lib/presentation/pages/main_scaffold.dart` — wrapped body in `Column` with conditional `MaterialBanner` for skew warning
- [x] **Step 4:** `TimeSyncNotifier` auto-initializes via Riverpod `build()` (no explicit init in `main.dart` needed)
- [x] **Step 5:** Added `bug_024_time_sync_banner_shows_on_skew` in `test/regression_test.dart`
- [x] **Step 6:** Added `bug_024_time_sync_no_banner_when_synced` in `test/regression_test.dart`
- [x] **Step 7:** `flutter analyze` — 0 issues
- [x] **Step 8:** `flutter test` — 6 passed, 0 failed
- [x] **Step 9:** Updated `Phase12_Roadmap.md` and `BUG_FIXING_DISCIPLINE.md` — BUG-024 Fixed

---

## Phase 12.3 — LLM Model Upgrade

- [x] **Step 1:** Updated `config/settings.py` and `domain/models/settings_model.py` — `llm_model` default changed to `gemini-2.5-flash`
- [x] **Step 2:** Updated `avalai_gateway.py` — added `classify_intent()` (JSON mode) and `smart_query()` (unified intent+SQL in one call)
- [x] **Step 3:** Updated `domain/services/llm_service.py` — added `classify_intent()` and `smart_query()` to `LLMService` protocol
- [x] **Step 4:** Updated `frigate_schema.py` — consolidated 20 SQL rules → 13 clean rules; removed repetitive sub_label rules 16-20 → single rule 13; removed rule 11 (forced `id` column)
- [x] **Step 5:** Updated `text_to_sql_use_case.py` — removed `_enrich_question()` entirely; `execute()` now passes raw user question to LLM
- [x] **Step 6:** Added `test_bug_025_llm_model_upgrade_sql_generation` and `test_bug_025_enrich_question_removed` in `tests/unit/use_cases/test_text_to_sql_use_case.py`
- [x] **Step 7:** `ruff check src/ tests/` — 0 errors; `python -m pytest tests/ -v` — 46 passed, 0 failed
- [x] **Step 8:** (Deployment deferred — container update will happen in Phase 12.7)
- [x] **Step 9:** Updated `Phase12_Roadmap.md` and `BUG_FIXING_DISCIPLINE.md` — BUG-025 Fixed

---

## Phase 12.4 — Intent Classification & Playback Deep Linking (Backend)

- [x] **Step 1:** Updated `api_models.py` — added `PlaybackIntent` model (`camera`, `start_time`, `end_time`, `date`); added `intent` and `playback_intent` fields to `QueryResponse`
- [x] **Step 2:** Updated `text_to_sql_use_case.py` — `execute()` and `execute_streaming()` now call `smart_query()` first; if `intent == 'playback_query'`, skips SQL execution and returns `PlaybackIntent` data; if `intent == 'event_query'`, uses returned SQL and executes against DB as usual; added `_build_playback_intent()` helper to parse ISO timestamps
- [x] **Step 3:** Updated `api_presenter.py` — `to_query_response()` now maps `intent` and `playback_intent` (as `PlaybackIntent` model) to API output
- [x] **Step 4:** Updated `api_controller.py` — streaming response meta now includes `intent` and `playback_intent` fields
- [x] **Step 5:** Added `test_bug_026_playback_intent_classification` and `test_bug_026_event_intent_still_works` in `tests/integration/test_api.py`
- [x] **Step 6:** `ruff check src/ tests/` — 0 errors; `python -m pytest tests/ -v` — 48 passed, 0 failed
- [x] **Step 7:** (Deployment deferred to Phase 12.7)
- [x] **Step 8:** Updated `Phase12_Roadmap.md` and `BUG_FIXING_DISCIPLINE.md` — BUG-026 Fixed

---

## Phase 12.5 — Playback Deep Linking (Flutter Frontend)

- [x] **Step 1:** Created `lib/presentation/models/playback_params.dart` — `PlaybackParams` data class with `fromJson()`, `==`/`hashCode`
- [x] **Step 2:** Created `lib/presentation/providers/navigation_provider.dart` — `NavigationState` (`mainTabIndex`, `nvrSubTabIndex`, `playbackParams`) + `NavigationNotifier` with `navigateToPlayback()`, `setMainTab()`, `setNvrSubTab()`
- [x] **Step 3:** Updated `chat_provider.dart` — added `intent`, `playbackIntent`, `isPlaybackQuery` getters to `ChatMessage`
- [x] **Step 4:** Updated `chat_bubble.dart` — converted to `ConsumerWidget`; added `_PlaybackDeepLinkButton` that calls `navigateToPlayback()` on tap
- [x] **Step 5:** Updated `main_scaffold.dart` — `ref.watch(navigationProvider)` for `mainTabIndex`; `ref.listenManual` for state changes; nav taps call `setMainTab()`
- [x] **Step 6:** Updated `classic_nvr_page.dart` — converted to `ConsumerStatefulWidget` with explicit `TabController`; `ref.listenManual` animates to `nvrSubTabIndex` on change
- [x] **Step 7:** Updated `playback_tab.dart` — `ref.listen(navigationProvider)` watches `playbackParams`; `_applyPlaybackParams()` sets camera/date, invalidates recording query, calls `_seekToStartTime()`
- [x] **Step 8:** Added `bug_027_playback_deep_link_navigates` in `test/regression_test.dart`
- [x] **Step 9:** Added `bug_027_playback_params_auto_select_camera` in `test/regression_test.dart`
- [x] **Step 10:** `flutter analyze` — 0 issues; `flutter test` — 8 passed, 0 failed
- [x] **Step 11:** Updated `Phase12_Roadmap.md` and `BUG_FIXING_DISCIPLINE.md` — BUG-027 Fixed

---

## Phase 12.6 — Inline Clip Playback for VOD Ranges

- [x] **Step 1:** Created `lib/presentation/widgets/inline_vod_player.dart` — `ConsumerStatefulWidget` with `media_kit` Player, `VideoController`, static `constructVodUrl()` method, 200px constrained height, rounded border, loading/error states
- [x] **Step 2:** Updated `lib/presentation/widgets/chat_bubble.dart` — renders `InlineVodPlayer` below `_PlaybackDeepLinkButton` for `playback_query` intent
- [x] **Step 3:** URL construction is handled via `InlineVodPlayer.constructVodUrl()` static method (no separate `api_client.dart` helper needed)
- [x] **Step 4:** Added `bug_028_inline_vod_player_constructs_url` in `test/regression_test.dart`
- [x] **Step 5:** `flutter analyze` — 0 issues; `flutter test` — 9 passed, 0 failed
- [x] **Step 6:** Updated `Phase12_Roadmap.md` and `BUG_FIXING_DISCIPLINE.md` — BUG-028 Fixed

---

## Phase 12.7 — Integration Testing & Deployment

- [ ] **Step 1:** Run `cd frigate-intelligence && python -m pytest tests/ -v` — all pass, count ≥ baseline + 8
- [ ] **Step 2:** Run `cd frigate-intelligence && ruff check src/ tests/` — 0 errors
- [ ] **Step 3:** Run `cd frigate_app && flutter analyze` — 0 issues
- [ ] **Step 4:** Run `cd frigate_app && flutter test` — all pass
- [ ] **Step 5:** Run `cd frigate_app && flutter build apk --debug` — success
- [ ] **Step 6:** Manual test on device — "Show me video 9am to 9:30am on cam1", "Was moein seen today?", "What happened last hour?"
- [ ] **Step 7:** Update `BUG_FIXING_DISCIPLINE.md` — finalize all Phase 12 Bug Registry entries
