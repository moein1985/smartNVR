# Phase 16: Web Panel Transformation & AI Report Builder

**Version:** 1.0  
**Date:** July 23, 2026  
**Author:** Cascade (GLM)  
**Status:** Proposal — Pending User Approval

---

## 1. Executive Summary

Phase 16 transforms the existing Next.js web panel (`frigate-web-panel`) from a
minimal chat/analytics shell into a **full Enterprise Dashboard** with sidebar
navigation, a dynamic multi-rule report scheduling engine, and intelligent
hardware orchestration UI with container capability validation.

**Key principle:** We do NOT reinvent Frigate's camera UI or CompreFace's face
management UI. Our panel focuses strictly on:
1. **Dashboard** — System stats and health overview
2. **Report Builder** — Dynamic multi-rule AI report scheduling
3. **Hardware Orchestrator** — Service-to-resource binding with validation
4. **System Settings** — Telegram/Bale/API configuration

---

## 2. Current State Analysis

### What Exists Today

| Component | Technology | Current State |
|-----------|-----------|---------------|
| `frigate-web-panel` | Next.js 16, React 19, Tailwind 4, TanStack Query 5 | Minimal: chat view, analytics page, settings page |
| `frigate_app` (Flutter) | Flutter, Riverpod, media_kit | Full mobile app with chat, NVR, settings, orchestrator page |
| Backend `CronService` | APScheduler `IntervalTrigger` | Single global report job, hardcoded prompt, Telegram-only |
| Backend `system_routes.py` | FastAPI | `/hardware`, `/containers`, `/assign`, `/frigate-config` endpoints |
| Backend `SettingsModel` | Pydantic | Single `report_interval_hours`, single Telegram destination |

### What Needs to Change

| Area | Current | Target |
|------|---------|--------|
| Web Panel Layout | Single-page, no sidebar | Dashboard shell with `NavigationSideBar` (RTL) |
| Report Scheduling | One global cron job | Multiple `ReportRule` entities, each with own schedule/destination |
| Hardware UI | Read-only display (Flutter only) | Interactive binding with GPU capability validation |
| Destinations | Telegram only | Telegram, Bale, extensible to SMS/Email |
| Zone Targeting | All zones in one prompt | Per-rule zone selection (`table_1`, `sensitive_area`, etc.) |

---

## 3. UI/UX Architecture

### 3.1 Web Panel Restructuring (Next.js)

The current `frigate-web-panel` will be restructured from a flat page structure
to a **dashboard shell with sidebar navigation**.

#### Proposed Route Structure

```
src/app/
├── layout.tsx                    # Root layout with Providers (QueryClient, ThemeProvider)
├── (dashboard)/
│   ├── layout.tsx                # Dashboard shell: Sidebar + Header + Main content area
│   ├── page.tsx                  # / → Redirect to /dashboard
│   ├── dashboard/
│   │   └── page.tsx              # /dashboard → Stats overview (health, CPU, RAM, GPU, containers)
│   ├── reports/
│   │   ├── page.tsx              # /reports → List of ReportRules + "Create Rule" button
│   │   └── [id]/
│   │       └── page.tsx          # /reports/[id] → Edit/create a specific ReportRule
│   ├── orchestrator/
│   │   └── page.tsx              # /orchestrator → Hardware + container binding UI
│   └── settings/
│       └── page.tsx              # /settings → Telegram/Bale/API config (existing, refactored)
├── chat/
│   └── page.tsx                  # /chat → Existing AI chat (preserved, linked from sidebar)
└── analytics/
    └── page.tsx                  # /analytics → Existing analytics (preserved, linked from sidebar)
```

#### Sidebar Component

```
┌──────────────────────────────────────────────────────────┐
│  [Logo] Frigate Intelligence                              │
│──────────────────────────────────────────────────────────│
│  📊 داشبورد          (/dashboard)                         │
│  📝 گزارش‌ساز         (/reports)                           │
│  🖥️ سخت‌افزار         (/orchestrator)                      │
│  ⚙️ تنظیمات           (/settings)                          │
│  💬 چپ هوش مصنوعی     (/chat)                              │
│  📈 تحلیل‌ها          (/analytics)                          │
│──────────────────────────────────────────────────────────│
│  [Server Status: ● Connected]                             │
│  [Clock Sync: ✓ Synced]                                   │
└──────────────────────────────────────────────────────────┘
```

- **RTL layout**: `dir="rtl"` on root layout, sidebar on the right
- **Responsive**: Sidebar collapses to a hamburger menu on screens < 768px
- **Active state**: Current route highlighted via `usePathname()` from `next/navigation`
- **Footer**: Live server health + clock sync status (reuse existing `useHealth` hook)

#### State Management

| Concern | Tool | Rationale |
|---------|------|-----------|
| Server state (API data) | TanStack Query 5 (already installed) | Caching, refetch, optimistic updates |
| Local UI state (forms, toggles) | React `useState` / `useReducer` | No complex client state needed |
| Theme/direction | Tailwind `dark:` + `dir="rtl"` on `<html>` | Already using Tailwind 4 |
| Report rules list | `useQuery(['report-rules'])` | Server-driven, cached |
| Hardware info | `useQuery(['hardware'])` with 5s polling | Real-time resource monitoring |

### 3.2 Flutter App Impact

The Flutter mobile app's `SettingsPage` (604 lines) is currently a monolithic
single-column page. We will **not** restructure the Flutter app's main
navigation (it already has a 3-tab `MainScaffold` with `NavigationRail` for
wide screens). Instead:

- The Flutter `OrchestratorPage` (Phase 15.2) already has hardware display —
  we'll add **interactive binding controls** alongside the read-only view
- The Flutter `SettingsPage` will get a **"Report Rules" section** that
  navigates to a new `ReportRulesPage` (list + create/edit)
- The Flutter app remains the **mobile companion**; the web panel is the
  **primary admin dashboard**

---

## 4. Backend Data Model

### 4.1 ReportRule Entity

We propose a new `ReportRule` model stored as a JSON file
(`data/report_rules.json`) — consistent with the existing `SettingsManager`
pattern. No SQLite migration needed.

```python
class ReportRule(BaseModel):
    """A single dynamic report rule with its own schedule and destination."""
    id: str                          # UUID4 hex
    name: str                        # Human-readable, e.g. "گزارش میز کار ۱"
    enabled: bool = True

    # Targeting
    zones: list[str] = []            # e.g., ["table_1", "sensitive_area_entrance"]
    cameras: list[str] = []          # e.g., ["cam1"] — empty = all cameras
    labels: list[str] = []           # e.g., ["person"] — empty = all labels

    # Schedule
    interval_hours: int = 24         # e.g., 6 = every 6 hours
    timezone: str = "Asia/Tehran"

    # Destination
    destination: str = "telegram"    # "telegram" | "bale" | "sms" (future)
    chat_id: str = ""                # Override global chat_id, or empty = use global

    # Report content
    prompt_template: str = ""        # Custom prompt, or empty = auto-generated from zones
    include_summary: bool = True     # Include AI-generated summary
    include_raw_data: bool = False   # Include raw event table

    # Metadata
    created_at: str = ""             # ISO timestamp
    last_run: str | None = None      # ISO timestamp of last execution
    last_status: str = ""            # "success" | "failed" | ""
```

### 4.2 ReportRuleManager

```python
class ReportRuleManager:
    """Manages persistence of ReportRules in data/report_rules.json."""

    def __init__(self, file_path: str = "data/report_rules.json"):
        self._file_path = Path(file_path)

    def list_rules(self) -> list[ReportRule]: ...
    def get_rule(self, rule_id: str) -> ReportRule | None: ...
    def create_rule(self, rule: ReportRule) -> ReportRule: ...
    def update_rule(self, rule_id: str, updates: dict) -> ReportRule: ...
    def delete_rule(self, rule_id: str) -> bool: ...
```

### 4.3 Multi-Rule Scheduler (CronService Evolution)

The existing `CronService` manages a single `"report_job"`. We propose
evolving it to manage **multiple jobs**, one per `ReportRule`:

```python
class ReportScheduler:
    """Manages APScheduler jobs for multiple ReportRules."""

    def __init__(
        self,
        rule_manager: ReportRuleManager,
        settings_manager: SettingsManager,
        container: Container,
    ):
        self._rule_manager = rule_manager
        self._settings_manager = settings_manager
        self._container = container
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        """Load all rules from disk and schedule each enabled one."""
        rules = self._rule_manager.list_rules()
        for rule in rules:
            if rule.enabled:
                self._schedule_rule(rule)
        self._scheduler.start()

    def _schedule_rule(self, rule: ReportRule) -> None:
        """Add or replace a single job for the given rule."""
        job_id = f"report_rule_{rule.id}"
        trigger = IntervalTrigger(hours=rule.interval_hours)
        self._scheduler.add_job(
            self._execute_rule,
            trigger=trigger,
            args=[rule.id],
            id=job_id,
            replace_existing=True,
        )

    def refresh_rule(self, rule_id: str) -> None:
        """Called after a rule is created/updated — reschedule that single job."""
        rule = self._rule_manager.get_rule(rule_id)
        job_id = f"report_rule_{rule_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
        if rule and rule.enabled:
            self._schedule_rule(rule)

    def remove_rule(self, rule_id: str) -> None:
        """Called after a rule is deleted — remove its job."""
        job_id = f"report_rule_{rule_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)

    async def _execute_rule(self, rule_id: str) -> None:
        """Execute a single report rule: generate prompt, query DB, send notification."""
        rule = self._rule_manager.get_rule(rule_id)
        if not rule or not rule.enabled:
            return
        # ... build prompt from rule.zones, execute via TextToSQLUseCase,
        #     format report, send via appropriate notifier,
        #     update rule.last_run and rule.last_status
```

### 4.4 Prompt Generation Per Rule

Instead of the current hardcoded `_build_report_prompt()`, each rule generates
its prompt dynamically:

```python
def _build_prompt_for_rule(rule: ReportRule) -> str:
    zones_str = ", ".join(rule.zones) if rule.zones else "all zones"
    cameras_str = ", ".join(rule.cameras) if rule.cameras else "all cameras"
    labels_str = ", ".join(rule.labels) if rule.labels else "all labels"

    if rule.prompt_template:
        return rule.prompt_template.format(
            zones=zones_str,
            cameras=cameras_str,
            labels=labels_str,
            interval=rule.interval_hours,
        )

    return (
        f"Summarize events for the past {rule.interval_hours} hours "
        f"for zones: {zones_str}. "
        f"Cameras: {cameras_str}. Labels: {labels_str}. "
        "Group by person/zone and provide total active hours and security alerts. "
        "Include first_seen, last_seen, and total_minutes for each person at a _table zone. "
        "List all detections in _sensitive zones with timestamps."
    )
```

### 4.5 New API Endpoints

```
GET    /api/v1/report-rules              → List all rules
POST   /api/v1/report-rules              → Create a new rule
GET    /api/v1/report-rules/{id}         → Get a specific rule
PUT    /api/v1/report-rules/{id}         → Update a rule
DELETE /api/v1/report-rules/{id}         → Delete a rule
POST   /api/v1/report-rules/{id}/test    → Trigger a rule immediately (test run)
GET    /api/v1/report-rules/{id}/history → Get execution history (future)
```

### 4.6 Notifier Abstraction

To support multiple destinations (Telegram, Bale, SMS), we introduce a
`Notifier` protocol:

```python
class Notifier(Protocol):
    async def send(self, notification: Notification) -> bool: ...

class TelegramNotifier:  # Already exists
    ...

class BaleNotifier:      # New — Bale messenger bot API
    async def send(self, notification: Notification) -> bool:
        # Bale Bot API: https://api.bale.ai/v1/bots/{token}/sendMessage
        ...

class NotifierFactory:
    @staticmethod
    def create(destination: str, settings: SettingsModel) -> Notifier:
        if destination == "telegram":
            return TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
        elif destination == "bale":
            return BaleNotifier(settings.bale_bot_token, settings.bale_chat_id)
        raise ValueError(f"Unknown destination: {destination}")
```

---

## 5. Hardware Validation Strategy

### 5.1 The Problem

When a user assigns a GPU to a service in the orchestrator UI, we must validate
that the service's Docker image actually supports GPU. For example:
- `frigate:0.18.0-beta1-tensorrt` → GPU-capable (has `deploy.resources.devices` in compose)
- `exadel/compreface:1.1.0-arcface-r100` → CPU-only (no GPU devices in compose)
- `frigate-intelligence:latest` → CPU-only (no GPU devices in compose)

### 5.2 Proposed Solution: Container Capability Discovery

We propose a `ContainerCapability` service that inspects running containers
and their images to determine GPU support:

```python
@dataclass
class ContainerCapability:
    name: str
    image: str
    supports_gpu: bool
    gpu_device_ids: list[str]
    reason: str  # "Has nvidia device reservations" or "No GPU devices configured"

class ContainerCapabilityChecker:
    """Determines if a container supports GPU by inspecting its Docker config."""

    # Known GPU-capable image patterns
    _GPU_IMAGE_PATTERNS = [
        "tensorrt",      # Frigate TensorRT builds
        "cuda",          # NVIDIA CUDA images
        "nvidia/",       # NVIDIA official images
    ]

    def check(self, container) -> ContainerCapability:
        # Strategy 1: Check deploy.resources.devices in compose config
        # (available via docker inspect → HostConfig.DeviceRequests)
        device_requests = getattr(container.attrs, "get", lambda *a: {})(
            "HostConfig", {}
        ).get("DeviceRequests", [])

        if device_requests:
            gpu_ids = []
            for req in device_requests:
                if req.get("Driver") == "nvidia":
                    gpu_ids.extend(req.get("DeviceIDs", []))
            return ContainerCapability(
                name=container.name,
                image=container.image.tags[0] if container.image.tags else "",
                supports_gpu=True,
                gpu_device_ids=gpu_ids,
                reason="Has nvidia device reservations",
            )

        # Strategy 2: Check image name for GPU patterns
        image_tag = container.image.tags[0] if container.image.tags else ""
        for pattern in self._GPU_IMAGE_PATTERNS:
            if pattern in image_tag.lower():
                return ContainerCapability(
                    name=container.name,
                    image=image_tag,
                    supports_gpu=True,
                    gpu_device_ids=[],
                    reason=f"Image name contains '{pattern}' (GPU-capable build)",
                )

        # Strategy 3: Default — CPU-only
        return ContainerCapability(
            name=container.name,
            image=image_tag,
            supports_gpu=False,
            gpu_device_ids=[],
            reason="No GPU devices configured and image is not a known GPU build",
        )
```

### 5.3 API Enhancement

Extend the existing `GET /api/v1/system/containers` response to include
capability info:

```json
{
  "containers": [
    {
      "name": "frigate",
      "image": "ghcr.io/blakeblackshear/frigate:0.18.0-beta1-tensorrt",
      "status": "running",
      "short_id": "abc123",
      "ports": [...],
      "capability": {
        "supports_gpu": true,
        "gpu_device_ids": ["0"],
        "reason": "Has nvidia device reservations"
      }
    },
    {
      "name": "compreface-core",
      "image": "exadel/compreface:1.1.0-arcface-r100",
      "status": "running",
      "short_id": "def456",
      "ports": [...],
      "capability": {
        "supports_gpu": false,
        "gpu_device_ids": [],
        "reason": "No GPU devices configured and image is not a known GPU build"
      }
    }
  ]
}
```

### 5.4 Frontend Validation

In the orchestrator UI:
1. Fetch `/api/v1/system/containers` — each container now has `capability.supports_gpu`
2. For each service row in the binding table:
   - If `supports_gpu == false`: GPU assignment dropdown is **disabled** (greyed out)
   - Show a warning tooltip: "این کانتینر از GPU پشتیبانی نمی‌کند (تصویر CPU-only)"
   - CPU and memory assignment remain available
3. If `supports_gpu == true`: GPU dropdown shows available GPU IDs from
   `/api/v1/system/hardware` response

---

## 6. Proposed Roadmap

### Sub-Phase 16.1: Web Panel Dashboard Shell (2–3 days)

**Goal:** Restructure the Next.js web panel into a sidebar-navigated dashboard.

- [ ] Step 1: Create `(dashboard)/layout.tsx` with RTL sidebar navigation
- [ ] Step 2: Create `/dashboard` page with system stats (health, CPU, RAM, GPU, containers)
- [ ] Step 3: Migrate existing `/settings` page into the dashboard shell
- [ ] Step 4: Migrate existing `/chat` and `/analytics` pages as sidebar links
- [ ] Step 5: Add responsive sidebar collapse for mobile (< 768px)
- [ ] Step 6: Add server health + clock sync indicator in sidebar footer
- [ ] Step 7: Tests + lint

### Sub-Phase 16.2: Report Rules Engine — Backend (3–4 days)

**Goal:** Multi-rule report scheduling with dynamic prompts and multiple destinations.

- [ ] Step 1: Create `ReportRule` model and `ReportRuleManager` (JSON persistence)
- [ ] Step 2: Create `BaleNotifier` for Bale messenger support
- [ ] Step 3: Create `NotifierFactory` abstraction
- [ ] Step 4: Evolve `CronService` → `ReportScheduler` (multi-job management)
- [ ] Step 5: Implement dynamic prompt generation per rule (`_build_prompt_for_rule`)
- [ ] Step 6: Add CRUD API endpoints (`/api/v1/report-rules`)
- [ ] Step 7: Add `POST /report-rules/{id}/test` for immediate test run
- [ ] Step 8: Integrate `ReportScheduler` with FastAPI lifespan (replace `CronService`)
- [ ] Step 9: Backend tests (rule CRUD, scheduler, prompt generation, notifier factory)
- [ ] Step 10: Lint + regression tests

### Sub-Phase 16.3: Report Builder UI — Web Panel (2–3 days)

**Goal:** Web UI for creating, editing, and testing report rules.

- [ ] Step 1: Create `/reports` page — list of rules with enable/disable toggle
- [ ] Step 2: Create `/reports/[id]` page — form for creating/editing a rule
  - Zone multi-select (fetched from `/api/v1/system/frigate-config` zones)
  - Camera multi-select (fetched from `/api/v1/cameras`)
  - Interval selector (1h, 6h, 12h, 24h, custom)
  - Destination dropdown (Telegram, Bale)
  - Custom prompt textarea (optional, with placeholder showing auto-generated prompt)
- [ ] Step 3: Add "Test Run" button that calls `POST /report-rules/{id}/test`
- [ ] Step 4: Add rule status indicators (last run, last status, next run time)
- [ ] Step 5: Tests + lint

### Sub-Phase 16.4: Hardware Orchestrator UI — Web Panel (2–3 days)

**Goal:** Interactive service-to-resource binding with GPU validation.

- [ ] Step 1: Implement `ContainerCapabilityChecker` in backend
- [ ] Step 2: Extend `GET /api/v1/system/containers` to include `capability` field
- [ ] Step 3: Create `/orchestrator` page in web panel:
  - Hardware overview cards (CPU cores, RAM, GPU cards)
  - Service binding table: one row per container
  - CPU core selector (checkboxes for cores 0–N)
  - GPU selector (dropdown, disabled if `supports_gpu == false`)
  - Memory limit input (GB)
  - Warning badges for CPU-only containers
- [ ] Step 4: "Apply" button calls `POST /api/v1/system/assign`
- [ ] Step 5: Show current override file contents (read-only preview)
- [ ] Step 6: Backend tests for capability checker
- [ ] Step 7: Tests + lint

### Sub-Phase 16.5: Flutter App Enhancements (2 days)

**Goal:** Bring report rules and interactive hardware binding to the mobile app.

- [ ] Step 1: Add `ReportRule` model and API client methods to Flutter
- [ ] Step 2: Create `ReportRulesPage` (list + create/edit) in Flutter
- [ ] Step 3: Add "Report Rules" navigation button in settings page
- [ ] Step 4: Enhance `OrchestratorPage` with interactive binding controls
- [ ] Step 5: Add GPU capability validation in Flutter (disable GPU dropdown for CPU-only)
- [ ] Step 6: Tests + lint

### Sub-Phase 16.6: Integration & Polish (1–2 days)

**Goal:** End-to-end testing, documentation, and deployment readiness.

- [ ] Step 1: End-to-end test: create rule → wait for schedule → verify Telegram/Bale delivery
- [ ] Step 2: End-to-end test: assign GPU to frigate → verify override file → restart container
- [ ] Step 3: Update `BUG_FIXING_DISCIPLINE.md` with Phase 16 entries
- [ ] Step 4: Update `Phase16_Roadmap.md` with completion checkmarks
- [ ] Step 5: Final lint + test sweep (backend + frontend + web panel)

---

## 7. Technology Decisions

### 7.1 Why JSON File for Report Rules (Not SQLite)?

| Factor | JSON File | SQLite Table |
|--------|-----------|-------------|
| Consistency with existing code | ✅ `SettingsManager` already uses JSON | ❌ Would need migration |
| Number of rules | Expected < 50 rules | Overkill for this scale |
| Atomic writes | `Path.write_text()` is sufficient | Requires transaction management |
| Querying | In-memory filtering is fine | Unnecessary complexity |
| Portability | Easy to copy in `data/` volume | Needs DB dump |

**Decision:** JSON file (`data/report_rules.json`), consistent with `data/settings.json`.

### 7.2 Why Not a Full SPA Router?

The web panel already uses Next.js 16 with the App Router. We leverage Next.js
route groups (`(dashboard)/`) for the dashboard shell without adding a separate
SPA router. This keeps SSR benefits and avoids client-side routing complexity.

### 7.3 Why Not Restructure Flutter's MainScaffold?

The Flutter app's 3-tab `MainScaffold` (AI, NVR, Settings) is well-suited for
mobile. Adding a 4th tab for "Reports" would clutter the bottom navigation.
Instead, we add report rules as a **pushed page** from Settings, similar to
how `OrchestratorPage` is accessed today.

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| APScheduler job ID collisions | Low | Medium | Use `report_rule_{uuid}` pattern |
| `report_rules.json` corruption | Low | High | Atomic write + backup on save |
| Bale API rate limits | Medium | Low | Exponential backoff (reuse existing retry pattern) |
| Container capability misclassification | Medium | Low | Fallback to image name pattern matching; manual override in UI |
| Web panel build complexity | Low | Medium | Reuse existing Tailwind 4 + TanStack Query setup |
| Flutter test coverage for new pages | Medium | Medium | Follow `BUG_FIXING_DISCIPLINE.md` Section 3 — regression test for each feature |

---

## 9. File Impact Summary

### New Files (Backend)

```
src/frigate_intelligence/
├── domain/models/
│   └── report_rule.py                    # ReportRule model
├── infrastructure/
│   ├── config/
│   │   └── report_rule_manager.py        # ReportRuleManager (JSON persistence)
│   ├── notifiers/
│   │   ├── bale_notifier.py              # BaleNotifier
│   │   └── notifier_factory.py           # NotifierFactory
│   ├── orchestrator/
│   │   └── container_capability.py       # ContainerCapabilityChecker
│   └── scheduler/
│       └── report_scheduler.py           # ReportScheduler (replaces CronService)
├── interface_adapters/controllers/
│   └── report_rule_controller.py         # CRUD API for report rules
└── infrastructure/api/routes/
    └── report_rule_routes.py             # FastAPI router for report rules
```

### New Files (Web Panel)

```
frigate-web-panel/src/
├── app/
│   ├── (dashboard)/
│   │   ├── layout.tsx                    # Dashboard shell with sidebar
│   │   ├── dashboard/page.tsx            # Stats overview
│   │   ├── reports/
│   │   │   ├── page.tsx                  # Rules list
│   │   │   └── [id]/page.tsx             # Rule editor
│   │   └── orchestrator/page.tsx         # Hardware binding UI
│   └── components/
│       ├── sidebar.tsx                   # Navigation sidebar (RTL)
│       ├── report-rule-form.tsx          # Reusable rule form
│       ├── hardware-overview.tsx         # CPU/RAM/GPU cards
│       └── service-binding-table.tsx     # Container-to-resource table
```

### New Files (Flutter)

```
frigate_app/lib/
├── data/models/
│   └── report_rule.dart                  # ReportRule model
├── presentation/
│   ├── pages/
│   │   └── report_rules_page.dart        # List + create/edit rules
│   └── providers/
│       └── report_rules_provider.dart    # Riverpod provider for rules
```

### Modified Files

| File | Change |
|------|--------|
| `system_routes.py` | Extend `/containers` to include `capability` field |
| `fastapi_app.py` | Replace `CronService` with `ReportScheduler` in lifespan |
| `api_controller.py` | Wire up `ReportRuleController` |
| `settings_model.py` | Add `bale_bot_token`, `bale_chat_id` fields (already partially present) |
| `api_client.dart` | Add report rule CRUD methods |
| `mock_api_client.dart` | Add mock report rule methods |
| `settings_page.dart` | Add "Report Rules" navigation button |
| `orchestrator_page.dart` | Add interactive binding controls with GPU validation |

---

## 10. Estimated Timeline

| Sub-Phase | Duration | Dependencies |
|-----------|----------|-------------|
| 16.1 — Web Panel Dashboard Shell | 2–3 days | None |
| 16.2 — Report Rules Engine (Backend) | 3–4 days | None |
| 16.3 — Report Builder UI (Web) | 2–3 days | 16.1 + 16.2 |
| 16.4 — Hardware Orchestrator UI (Web) | 2–3 days | 16.1 |
| 16.5 — Flutter App Enhancements | 2 days | 16.2 + 16.4 |
| 16.6 — Integration & Polish | 1–2 days | All above |
| **Total** | **12–17 days** | |

---

## 11. Open Questions for User

1. **Bale Messenger:** Do you have a Bale bot token and chat ID for testing,
   or should we stub the `BaleNotifier` and test only with Telegram?

2. **Zone Discovery:** Should the web panel fetch zones from
   `/api/v1/system/frigate-config` (which reads `frigate.yml`), or should we
   add a dedicated `/api/v1/zones` endpoint that returns annotated zones
   (workstation vs. restricted)?

3. **Report History:** Do you want to persist execution history (last N runs
   per rule with timestamps and status), or is `last_run` + `last_status`
   on the rule itself sufficient for Phase 16?

4. **SMS Gateway:** Is there a specific SMS gateway/provider you plan to use,
   or should we leave SMS as a future extension point?

5. **Web Panel Auth:** Should the web panel have authentication (login page),
   or is it behind a network firewall / VPN only?

---

## 12. Conclusion

Phase 16 transforms the web panel from a minimal chat shell into a proper
enterprise admin dashboard while keeping the backend architecture clean and
consistent with existing patterns (JSON persistence, APScheduler, Clean
Architecture). The dynamic report rules engine replaces the single global
cron job with a flexible multi-rule system, and the hardware validation
strategy ensures users can't misconfigure GPU assignments for CPU-only
containers.

We await your feedback on the open questions before finalizing the roadmap
and beginning execution.
