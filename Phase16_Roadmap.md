# Phase 16: Web Panel Transformation & AI Report Builder — Roadmap

**Status:** Approved — Ready for Execution  
**Date:** July 23, 2026

---

## User Directives (Binding Constraints)

1. **Bale:** Implement `BaleNotifier` backend, skip E2E testing for now.
2. **Zones:** Read from `frigate.yml` directly. Rely on `_table`/`_sensitive` suffix logic. LLM must correlate zone names with face sub-labels (e.g., `ahmad_table` + sub_label `ahmad`). Add "Working Hours" setting (e.g., 08:00–16:00).
3. **Report History:** Store last 100 executed reports in `data/report_history.json`.
4. **SMS:** Skip. Telegram + Bale only. Kavenegar is future extension point.
5. **Auth (RBAC):** Login page required. Roles: `admin` (full access), `user` (Chat/AI only). User Management in Settings. Seed: `admin`/`admin` (undeletable), `user`/`user`.
6. **Theme:** Web panel must mirror Flutter app — dark theme, cyan seed color, Material 3 aesthetic, rounded corners (28px cards, 24px inputs/buttons).

---

## Discipline Compliance (BUG_FIXING_DISCIPLINE.md)

Every sub-phase in this roadmap adheres to the following discipline rules:

### 1. Regression-First (Section 1)
- Before starting any sub-phase, record baseline: `python -m pytest tests/ --co -q | wc -l` and `flutter test --reporter compact 2>&1 | tail -1`
- Test count must **never decrease**. If a test is removed, it must be replaced with an equivalent or stronger test.

### 2. Regression Test Naming (Section 3)
- Backend tests: `test_feat_016_<subphase>_<description>` (e.g., `test_feat_016_1_auth_login_success`)
- Flutter tests: `feat_016_<subphase>_<description>` (e.g., `feat_016_7_report_rules_page_renders`)
- Every new feature must include a regression test that would fail without the implementation.

### 3. Minimal Change & Architecture (Section 4)
- Preserve Clean Architecture layering: `domain/` → `use_cases/` → `interface_adapters/` → `infrastructure/`
- One feature per commit. No unrelated refactoring.
- New dependencies must be explicitly justified:
  - `bcrypt` — password hashing for auth (justified: security requirement for RBAC)
  - `PyJWT` — JWT token generation/verification (justified: stateless auth for web panel)
  - No other new dependencies unless approved.

### 4. No Silent Failures (Section 5)
- All new backend modules must use `logging.getLogger(__name__)` and log errors with `exc_info=True`
- All new Flutter modules must use `debugPrint('[Prefix] ...')` in catch blocks
- New logging prefixes to register in `BUG_FIXING_DISCIPLINE.md` Section 5 table:
  | Component | Prefix | Example |
  |-----------|--------|---------|
  | Auth | `[Auth]` | `[Auth] Login failed for user 'admin': invalid password` |
  | Report Scheduler | `[ReportScheduler]` | `[ReportScheduler] Executing rule 'abc123': ...` |
  | Bale Notifier | `[BaleNotifier]` | `[BaleNotifier] Send failed (attempt 1/3): ...` |
  | Report Rules | `[ReportRules]` | `[ReportRules] Created rule 'گزارش میز ۱'` |
  | User Manager | `[UserManager]` | `[UserManager] Seeded default admin user` |
  | Container Capability | `[ContainerCapability]` | `[ContainerCapability] frigate: GPU-capable (DeviceRequests)` |

### 5. Deployment Gate (Section 6)
- The existing deployment checklist is extended with Web Panel checks:
  | Check | Command | Required Result |
  |-------|---------|-----------------|
  | Web panel lint | `cd frigate-web-panel && npm run lint` | 0 errors |
  | Web panel build | `cd frigate-web-panel && npm run build` | Success |
  | Web panel reachable | `curl -s http://192.168.85.203:3000` | 200 OK |
- If **any** check in the full deployment gate fails, deployment is blocked.

### 6. Bug Registry (Section 7)
- Each completed sub-phase gets a `FEAT-016.x` entry in the Bug Registry table
- Format: `FEAT-016.<subphase> | <date> | <description> | <root cause / motivation> | <fix / implementation> | <regression test> | <status>`

### 7. Pre-Phase Checklist (Section 8 analog)
Before starting each sub-phase, verify:
- [ ] Baseline test count recorded (backend + Flutter)
- [ ] `ruff check src/ tests/` passes
- [ ] `python -m pytest tests/` passes
- [ ] `flutter analyze` — 0 issues
- [ ] `flutter test` — all pass
- [ ] `npm run lint` — 0 errors (for web panel sub-phases)

---

## Sub-Phase 16.1: Authentication & Dashboard Shell

### Pre-Phase Baseline
- [x] Record baseline: `python -m pytest tests/ --co -q` count (122), `flutter test` pass count (25), `npm run lint` status (0 errors)

### Backend — Auth

- [x] Step 1: Create `UserModel` (id, username, password_hash, role, created_at) in `domain/models/user_model.py` — **domain layer, no external deps**
- [x] Step 2: Create `UserManager` (JSON persistence in `data/users.json`) in `infrastructure/config/user_manager.py`
- [x] Step 3: Seed default users on startup: `admin`/`admin` (role=admin, undeletable), `user`/`user` (role=user)
- [x] Step 4: Create `AuthService` (password hashing with `bcrypt`, JWT token generation/verification) in `infrastructure/auth/auth_service.py`
- [x] Step 5: Create `auth_routes.py` with `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`
- [x] Step 6: Create `get_current_user` FastAPI dependency for protected routes
- [x] Step 7: Create `require_admin` dependency that checks `role == "admin"`
- [x] Step 8: Add user management endpoints: `GET /api/v1/users`, `POST /api/v1/users`, `PUT /api/v1/users/{id}`, `DELETE /api/v1/users/{id}` (admin-only, prevent deleting seed admin)
- [x] Step 9: Backend tests for auth — naming: `test_feat_016_1_auth_login_success`, `test_feat_016_1_auth_login_invalid_password`, `test_feat_016_1_auth_token_verify`, `test_feat_016_1_auth_role_check_admin`, `test_feat_016_1_auth_role_check_user_denied`, `test_feat_016_1_user_crud_create`, `test_feat_016_1_user_crud_delete`, `test_feat_016_1_user_seed_admin_undeletable`
- [x] Step 10: Verify all errors logged with `[Auth]` / `[UserManager]` prefix — no silent failures
- [x] Step 11: Lint (`ruff check`) + regression (`pytest` — 141 passed, count ≥ baseline of 122)

### Web Panel — Theme & Shell

- [x] Step 11: Update `globals.css` with Flutter-mirrored dark theme: `--background: #0a0a0a`, cyan-600 primary (`#0891b2`), gray-800 cards, rounded-2xl (28px) cards, rounded-xl (24px) inputs
- [x] Step 12: Create `src/lib/auth-context.tsx` — client-side auth state (token in localStorage, user info, login/logout functions)
- [x] Step 13: Create `src/app/login/page.tsx` — login form (username/password, RTL, cyan theme)
- [x] Step 14: Create `src/middleware.ts` — Next.js middleware to redirect unauthenticated users to `/login` (except `/login` itself)
- [x] Step 15: Create `src/app/(dashboard)/layout.tsx` — dashboard shell with RTL sidebar
- [x] Step 16: Create `src/components/sidebar.tsx` — navigation sidebar with role-based links:
  - `admin`: Dashboard, Reports, Orchestrator, Settings, User Management, Chat, Analytics
  - `user`: Chat only
  - RTL: sidebar on right side
  - Responsive: collapses to hamburger on < 768px
  - Footer: server health + clock sync status
- [x] Step 17: Create `src/app/(dashboard)/dashboard/page.tsx` — stats overview (CPU, RAM, GPU, containers, health)
- [x] Step 18: Migrate existing `/settings` and `/analytics` pages into `(dashboard)/` route group
- [x] Step 19: Move `/` chat page into `(dashboard)/chat/page.tsx`
- [x] Step 21: Web panel lint (`npm run lint`) + build (`npm run build`) verification — 0 errors, build success

---

## Sub-Phase 16.2: Report Rules Engine & History (Backend)

### Pre-Phase Baseline
- [x] Record baseline: `python -m pytest tests/ --co -q` count (141)

### Data Models

- [x] Step 1: Create `ReportRule` model in `domain/models/report_rule.py`:
  - `id`, `name`, `enabled`, `zones[]`, `cameras[]`, `labels[]`
  - `interval_hours`, `timezone`, `destination` (telegram|bale), `chat_id`
  - `prompt_template`, `include_summary`, `include_raw_data`
  - `created_at`, `last_run`, `last_status`
- [x] Step 2: Create `ReportHistoryEntry` model in `domain/models/report_history.py`:
  - `id`, `rule_id`, `rule_name`, `executed_at`, `status`, `message_preview`, `destination`
- [x] Step 3: Add `work_hours_start: str = "08:00"` and `work_hours_end: str = "16:00"` to `SettingsModel`

### Persistence

- [x] Step 4: Create `ReportRuleManager` in `infrastructure/config/report_rule_manager.py` (JSON, `data/report_rules.json`)
- [x] Step 5: Create `ReportHistoryManager` in `infrastructure/config/report_history_manager.py` (JSON, `data/report_history.json`, max 100 entries, FIFO eviction)

### Notifiers

- [x] Step 6: Create `BaleNotifier` in `infrastructure/notifiers/bale_notifier.py` (Bale Bot API: `https://api.bale.ai/v1/bots/{token}/sendMessage`)
- [x] Step 7: Create `NotifierFactory` in `infrastructure/notifiers/notifier_factory.py` (dispatch to Telegram or Bale based on destination string)

### Scheduler

- [x] Step 8: Create `ReportScheduler` in `infrastructure/scheduler/report_scheduler.py`:
  - Replaces `CronService` — manages multiple APScheduler jobs (`report_rule_{id}`)
  - `start()`: load all rules, schedule each enabled one
  - `refresh_rule(rule_id)`: reschedule single rule after create/update
  - `remove_rule(rule_id)`: remove job after delete
  - `_execute_rule(rule_id)`: build prompt → query DB → format → send via notifier → record history
- [x] Step 9: Implement dynamic prompt generation per rule:
  - Auto-generate from zones/cameras/labels if `prompt_template` is empty
  - Include working hours context from `SettingsModel`
  - Zone-name-to-sub-label correlation hints (e.g., "zone `ahmad_table` likely tracks person `ahmad`")
- [x] Step 10: Wire `ReportScheduler` into FastAPI lifespan (replace `CronService`)

### API Endpoints

- [x] Step 11: Create `report_rule_routes.py`:
  - `GET /api/v1/report-rules` — list all rules (admin)
  - `POST /api/v1/report-rules` — create rule (admin)
  - `GET /api/v1/report-rules/{id}` — get rule (admin)
  - `PUT /api/v1/report-rules/{id}` — update rule (admin)
  - `DELETE /api/v1/report-rules/{id}` — delete rule (admin)
  - `POST /api/v1/report-rules/{id}/test` — trigger immediate test run (admin)
  - `GET /api/v1/report-rules/{id}/history` — get execution history for rule (admin)
  - `GET /api/v1/report-history` — get all recent history (admin)
- [x] Step 12: Add `work_hours_start`/`work_hours_end` to settings PUT/GET endpoints

### Tests

- [x] Step 13: Backend tests — naming: `test_feat_016_2_rule_crud_create`, `test_feat_016_2_rule_crud_update`, `test_feat_016_2_rule_crud_delete`, `test_feat_016_2_scheduler_multi_job`, `test_feat_016_2_prompt_generation_zones`, `test_feat_016_2_prompt_generation_working_hours`, `test_feat_016_2_history_fifo_eviction`, `test_feat_016_2_notifier_factory_telegram`, `test_feat_016_2_notifier_factory_bale`, `test_feat_016_2_bale_notifier_structure`
- [x] Step 14: Verify all errors logged with `[ReportScheduler]` / `[BaleNotifier]` / `[ReportRules]` prefix — no silent failures
- [x] Step 15: Lint (`ruff check`) + regression (`pytest` — 158 passed, count ≥ baseline of 141)

---

## Sub-Phase 16.3: Report Builder UI (Web Panel)

- [x] Step 1: Create `src/lib/report-rules-api.ts` — API client functions for rule CRUD + history
- [x] Step 2: Create `src/hooks/use-report-rules.ts` — TanStack Query hooks for rules list
- [x] Step 3: Create `src/app/(dashboard)/reports/page.tsx` — rules list page:
  - Table: name, zones, interval, destination, enabled toggle, last run, last status
  - "Create Rule" button → navigates to `/reports/new`
  - "Test Run" button per rule
  - "History" button per rule → navigates to `/reports/{id}/history`
- [x] Step 4: Create `src/app/(dashboard)/reports/[id]/page.tsx` — rule editor form:
  - Name input
  - Zone multi-select (fetched from `/api/v1/system/frigate-config` → parse zone keys)
  - Camera multi-select (fetched from `/api/v1/cameras`)
  - Label multi-select (person, car, etc.)
  - Interval selector (1h, 6h, 12h, 24h, custom)
  - Destination dropdown (Telegram, Bale)
  - Custom prompt textarea (optional, with placeholder showing auto-generated prompt)
  - Enable/disable toggle
  - Save + Delete buttons
- [x] Step 5: Create `src/app/(dashboard)/reports/[id]/history/page.tsx` — execution history table:
  - Date/time, status, destination, message preview (truncated)
  - Last 100 entries
- [x] Step 6: Create `src/components/report-rule-form.tsx` — reusable form component
- [x] Step 8: Verify no silent failures in web panel API calls (console.error for failed requests)
- [x] Step 9: Web panel lint (`npm run lint`) + build (`npm run build`) — 0 errors, build success

---

## Sub-Phase 16.4: Hardware Orchestrator UI (Web Panel + Backend)

### Pre-Phase Baseline
- [ ] Record baseline: `python -m pytest tests/ --co -q` count

### Backend

- [ ] Step 1: Create `ContainerCapabilityChecker` in `infrastructure/orchestrator/container_capability.py`:
  - Strategy 1: Check `HostConfig.DeviceRequests` for nvidia driver
  - Strategy 2: Match image name patterns (`tensorrt`, `cuda`, `nvidia/`)
  - Strategy 3: Default CPU-only
- [ ] Step 2: Extend `GET /api/v1/system/containers` to include `capability` field per container
- [ ] Step 3: Backend tests — naming: `test_feat_016_4_capability_gpu_container`, `test_feat_016_4_capability_cpu_container`, `test_feat_016_4_capability_pattern_match_tensorrt`, `test_feat_016_4_capability_pattern_match_cuda`
- [ ] Step 3b: Verify all errors logged with `[ContainerCapability]` prefix — no silent failures

### Web Panel

- [ ] Step 4: Create `src/hooks/use-hardware.ts` — TanStack Query hook (5s polling)
- [ ] Step 5: Create `src/hooks/use-containers.ts` — TanStack Query hook
- [ ] Step 6: Create `src/app/(dashboard)/orchestrator/page.tsx`:
  - Hardware overview cards: CPU cores + utilization, RAM total/available, GPU cards (name, memory, utilization)
  - Service binding table: one row per container
  - Per row: container name, image, status, CPU core checkboxes, GPU dropdown (disabled if `supports_gpu == false` + warning badge), memory limit input
  - "Apply" button → calls `POST /api/v1/system/assign`
  - Current override file preview (read-only)
- [ ] Step 7: Create `src/components/hardware-overview.tsx` — reusable hardware cards
- [ ] Step 8: Create `src/components/service-binding-table.tsx` — binding table with GPU validation
- [ ] Step 10: Web panel lint (`npm run lint`) + build (`npm run build`) — 0 errors

---

## Sub-Phase 16.5: User Management UI (Web Panel)

- [ ] Step 1: Create `src/lib/users-api.ts` — API client for user CRUD
- [ ] Step 2: Create `src/hooks/use-users.ts` — TanStack Query hooks
- [ ] Step 3: Create `src/app/(dashboard)/settings/users/page.tsx` — user management table:
  - Columns: username, role, created_at, actions (edit, delete)
  - "Add User" button → modal with username/password/role form
  - Seed admin row: delete button disabled, tooltip "حذف‌نشدنی"
  - Edit user: change password, change role
- [ ] Step 4: Integrate user management as a tab/section within Settings page
- [ ] Step 6: Web panel lint (`npm run lint`) + build (`npm run build`) — 0 errors

---

## Sub-Phase 16.6: Working Hours & LLM Intelligence (Backend)

### Pre-Phase Baseline
- [ ] Record baseline: `python -m pytest tests/ --co -q` count

- [ ] Step 1: Update `frigate_schema.py` SQL rules to include working hours context:
  - Rule: "If working hours are 08:00–16:00, queries about 'how long was X at desk' should filter events between those hours"
  - Rule: "Zone names with `_table` suffix correspond to workstations. If zone is `ahmad_table` and sub_label is `ahmad`, they refer to the same person."
- [ ] Step 2: Update `load_schema_context()` to inject `work_hours_start`/`work_hours_end` from settings into the LLM schema context
- [ ] Step 3: Update `_build_prompt_for_rule()` to include working hours in generated prompts
- [ ] Step 4: Update `SAMPLE_QUERIES` with working-hours examples (e.g., "How long was Ahmad at his desk today during working hours?")
- [ ] Step 5: Backend tests — naming: `test_feat_016_6_working_hours_in_prompt`, `test_feat_016_6_working_hours_in_schema_context`, `test_feat_016_6_zone_name_correlation_hint`
- [ ] Step 6: Lint (`ruff check`) + regression (`pytest` — count ≥ baseline)

---

## Sub-Phase 16.7: Flutter App Enhancements

### Pre-Phase Baseline
- [ ] Record baseline: `flutter test` pass count, `flutter analyze` issue count

- [ ] Step 1: Add `ReportRule` model to Flutter (`lib/data/models/report_rule.dart`)
- [ ] Step 2: Add report rule CRUD methods to `api_client.dart` + `mock_api_client.dart`
- [ ] Step 3: Create `report_rules_provider.dart` (Riverpod)
- [ ] Step 4: Create `report_rules_page.dart` (list + create/edit, RTL Persian)
- [ ] Step 5: Add "Report Rules" navigation button in `settings_page.dart`
- [ ] Step 6: Enhance `orchestrator_page.dart` with interactive binding controls (CPU checkboxes, GPU dropdown with validation, memory input)
- [ ] Step 7: Add `work_hours_start`/`work_hours_end` fields to Flutter settings page
- [ ] Step 8: Update all test mock clients with new API methods (`_SyncedMockClient`, `_SkewableMockApiClient`, `_MaintenanceMockClient`, `_OrchestratorMockClient`)
- [ ] Step 9: Flutter tests — naming: `feat_016_7_report_rules_page_renders`, `feat_016_7_report_rules_create_form`, `feat_016_7_orchestrator_interactive_binding`, `feat_016_7_gpu_disabled_for_cpu_only`
- [ ] Step 10: Verify all catch blocks use `debugPrint('[ReportRules] ...')` / `debugPrint('[Orchestrator] ...')` — no silent failures
- [ ] Step 11: `flutter analyze` — 0 issues + `flutter test` — all pass, count ≥ baseline

---

## Sub-Phase 16.8: Integration & Polish

- [ ] Step 1: E2E test: login as admin → create report rule → test run → verify Telegram delivery
- [ ] Step 2: E2E test: login as user → verify only Chat page accessible
- [ ] Step 3: E2E test: assign GPU to frigate → verify override file → verify container restart
- [ ] Step 4: E2E test: verify CPU-only container GPU dropdown is disabled in UI
- [ ] Step 5: E2E test: verify report history records last 100 entries with FIFO
- [ ] Step 6: Update `BUG_FIXING_DISCIPLINE.md`:
  - Add `FEAT-016.1` through `FEAT-016.8` entries to Bug Registry table (Section 7)
  - Add new logging prefixes (`[Auth]`, `[ReportScheduler]`, `[BaleNotifier]`, `[ReportRules]`, `[UserManager]`, `[ContainerCapability]`) to Section 5 table
  - Add Web Panel deployment gate rows to Section 6 table
- [ ] Step 7: Update `Phase16_Roadmap.md` with completion checkmarks
- [ ] Step 8: Final deployment gate sweep — ALL must pass:
  | Check | Command | Required |
  |-------|---------|----------|
  | Backend lint | `cd frigate-intelligence && ruff check src/ tests/` | 0 errors |
  | Backend tests | `cd frigate-intelligence && python -m pytest tests/` | All pass, count ≥ baseline |
  | Flutter analyze | `cd frigate_app && flutter analyze` | 0 issues |
  | Flutter tests | `cd frigate_app && flutter test` | All pass |
  | Web panel lint | `cd frigate-web-panel && npm run lint` | 0 errors |
  | Web panel build | `cd frigate-web-panel && npm run build` | Success |
- [ ] Step 9: Grand finale note

---

## Theme Specification (Flutter Mirror)

| Token | Flutter Value | Tailwind Equivalent |
|-------|--------------|-------------------|
| Seed color | `Colors.cyan` | `cyan-600` (#0891b2) |
| Brightness | `Brightness.dark` | `dark` mode |
| Background | `colorScheme.surface` | `gray-950` (#0a0a0a) |
| Card background | `colorScheme.surfaceContainer` | `gray-800` (#1f2937) |
| Card border radius | 28px | `rounded-3xl` (28px) |
| Input border radius | 24px | `rounded-2xl` (24px) |
| Button border radius | 24px | `rounded-2xl` (24px) |
| Focused border | `colorScheme.primary` width 2 | `border-cyan-600 ring-1 ring-cyan-600` |
| Divider | `outlineVariant` alpha 0.3 | `border-gray-700/30` |

---

## File Impact Summary

### New Backend Files
```
src/frigate_intelligence/
├── domain/models/
│   ├── report_rule.py
│   ├── report_history.py
│   └── user_model.py
├── infrastructure/
│   ├── auth/auth_service.py
│   ├── config/
│   │   ├── report_rule_manager.py
│   │   ├── report_history_manager.py
│   │   └── user_manager.py
│   ├── notifiers/
│   │   ├── bale_notifier.py
│   │   └── notifier_factory.py
│   ├── orchestrator/container_capability.py
│   └── scheduler/report_scheduler.py
├── interface_adapters/controllers/
│   └── report_rule_controller.py
└── infrastructure/api/routes/
    ├── auth_routes.py
    ├── user_routes.py
    └── report_rule_routes.py
```

### New Web Panel Files
```
frigate-web-panel/src/
├── app/
│   ├── login/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   ├── dashboard/page.tsx
│   │   ├── reports/
│   │   │   ├── page.tsx
│   │   │   ├── [id]/page.tsx
│   │   │   └── [id]/history/page.tsx
│   │   ├── orchestrator/page.tsx
│   │   └── settings/users/page.tsx
├── components/
│   ├── sidebar.tsx
│   ├── hardware-overview.tsx
│   ├── service-binding-table.tsx
│   └── report-rule-form.tsx
├── hooks/
│   ├── use-report-rules.ts
│   ├── use-hardware.ts
│   ├── use-containers.ts
│   └── use-users.ts
└── lib/
    ├── auth-context.tsx
    ├── report-rules-api.ts
    └── users-api.ts
```

### New Flutter Files
```
frigate_app/lib/
├── data/models/report_rule.dart
├── presentation/
│   ├── pages/report_rules_page.dart
│   └── providers/report_rules_provider.dart
```

### Modified Files
| File | Change |
|------|--------|
| `fastapi_app.py` | Replace CronService with ReportScheduler, add auth/user/report routes |
| `system_routes.py` | Add capability field to /containers |
| `settings_model.py` | Add work_hours_start, work_hours_end |
| `frigate_schema.py` | Add working hours + zone-name correlation rules |
| `api_client.dart` | Add report rule + user methods |
| `settings_page.dart` | Add working hours fields, report rules button |
| `orchestrator_page.dart` | Add interactive binding controls |
| `globals.css` | Flutter-mirrored dark cyan theme |
| `layout.tsx` | Add AuthProvider wrapper |
