# Phase 12 — Technical Feasibility Proposal

**Time Synchronization & LLM-Driven Playback Search**

**Version:** 1.0  
**Date:** July 21, 2026  
**Author:** GLM (Architecture Analysis)  
**Scope:** `frigate-intelligence` (Python/FastAPI backend) + `frigate_app` (Flutter/Riverpod frontend)

---

## Table of Contents

1. [Feasibility Assessment](#1-feasibility-assessment)
2. [LLM Model Upgrade Analysis](#2-llm-model-upgrade-analysis)
3. [GLM's Architectural Recommendations](#3-glms-architectural-recommendations)
4. [Actionable Step-by-Step Execution Plan](#4-actionable-step-by-step-execution-plan)

---

## 1. Feasibility Assessment

### 1.1 Server Docker Container Timezone/NTP Configuration

**Current State (verified via SSH):**

| Component | Timezone | Time at 18:10 UTC |
|-----------|----------|-------------------|
| Host OS (`192.168.85.203`) | UTC (no `/etc/timezone` file) | `Tue Jul 21 18:11 UTC 2026` |
| `frigate` container | UTC (no `TZ` env var) | `Tue Jul 21 18:10 UTC 2026` |
| `frigate-intelligence` container | UTC (no `TZ` env var) | `Tue Jul 21 18:10 UTC 2026` |

**Key Finding:** Both containers run in UTC. The user's phone (Iran, UTC+3:30) is **+3:30 ahead** of server time. This is not "skew" in the NTP sense — it's a legitimate timezone offset. However, true clock skew (NTP drift) is also possible and should be detected.

**Proposed `/api/v1/health` Enhancement:**

Current `HealthResponse` (`api_models.py:41-44`):
```python
class HealthResponse(BaseModel):
    status: str
    version: str
    db_connected: bool
```

Proposed:
```python
class HealthResponse(BaseModel):
    status: str
    version: str
    db_connected: bool
    server_timestamp: float       # Unix epoch seconds (UTC)
    server_timezone: str          # "UTC" or "Asia/Tehran"
    server_datetime_iso: str      # ISO 8601 with offset, e.g. "2026-07-21T18:10:51+00:00"
```

**Implementation in `api_controller.py:93-96`:**
```python
async def health(self) -> HealthResponse:
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    return HealthResponse(
        status="ok",
        version="0.1.0",
        db_connected=True,
        server_timestamp=now.timestamp(),
        server_timezone="UTC",
        server_datetime_iso=now.isoformat(),
    )
```

**Feasibility:** Trivial. No new dependencies, no architectural changes. The Flutter client already calls `health()` via `ApiClient.health()` (`api_client.dart:68-71`).

### 1.2 Flutter `TimeSyncNotifier` Architecture & Banner Placement

**Proposed Architecture:**

```
lib/presentation/providers/
├── time_sync_provider.dart    # NEW: TimeSyncNotifier + skew detection
└── server_config_provider.dart  # EXISTING: provides ApiClient
```

**`TimeSyncNotifier` Design:**

```dart
class TimeSyncState {
  final Duration? skew;          // client time - server time (positive = client ahead)
  final DateTime? serverTime;
  final bool isChecking;
  final String? error;
  
  bool get hasSignificantSkew => skew != null && skew!.abs() > const Duration(minutes: 2);
}
```

The notifier will:
1. Call `ApiClient.health()` on app startup and periodically (every 5 minutes).
2. Compare `server_timestamp` from response with local `DateTime.now().millisecondsSinceEpoch / 1000`.
3. Expose `hasSignificantSkew` for the UI banner.

**Banner Placement in `MainScaffold`:**

The `MainScaffold` (`main_scaffold.dart`) uses `IndexedStack` for page switching. The warning banner should be placed **above** the `IndexedStack` so it's visible on all tabs:

```dart
// In MainScaffold build():
return Scaffold(
  body: Column(
    children: [
      if (timeSyncState.hasSignificantSkew) _buildSkewBanner(),
      Expanded(child: _buildNavLayout()),  // existing LayoutBuilder
    ],
  ),
);
```

**Feasibility:** High. Riverpod `Notifier` pattern is already used throughout the app (`ChatNotifier`, `ServerConfigNotifier`). The banner is a simple `MaterialBanner` widget.

### 1.3 Backend Schema Changes: Event Queries vs Playback VOD Ranges

**Current State:**

The LLM generates SQL against the `event` table (detections with `id`, `label`, `camera`, `start_time`, `end_time`, `sub_label`, `zones`). The `recordings` table stores 10-second MP4 segments (`path`, `start_time`, `end_time`, `duration`, `objects`, `motion`).

**The Problem:** When a user says "Show me video between 9:00 AM and 9:30 AM on cam1", the LLM currently generates a `SELECT` against the `recordings` table, but the Flutter app has no way to distinguish this from an event query. The `ChatMessage.queryResult` contains generic `columns` and `rows` — the frontend checks `hasEvents` by looking for an `id` column (`chat_provider.dart:11-18`), but recordings also have an `id` column, creating ambiguity.

**Proposed Solution: Intent Classification Layer**

Add a lightweight intent classification step **before** SQL generation. The LLM (or a fast regex pre-check) classifies the question into one of:

| Intent | Target | Action |
|--------|--------|--------|
| `event_query` | `event` table | Return rows as-is (existing behavior) |
| `playback_query` | `recordings` table or Frigate VOD API | Return a `playback_intent` payload with camera, start_time, end_time |
| `analytics_query` | Aggregations on `event` table | Return rows as-is |

**Two approaches for classification:**

**Approach A — LLM-based (recommended with Flash upgrade):**

Add a `classify_intent` method to `AvalaiGateway` that asks the LLM to return a JSON tag before generating SQL:

```python
def classify_intent(self, question: str) -> dict:
    response = self._client.chat.completions.create(
        model=self._model,
        messages=[
            {"role": "system", "content": INTENT_CLASSIFICATION_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0.0,
        max_tokens=100,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
```

Returns: `{"intent": "playback_query", "camera": "cam1", "start_time": "2026-07-21T09:00:00+03:30", "end_time": "2026-07-21T09:30:00+03:30"}`

**Approach B — Regex pre-check (fallback, no extra LLM call):**

```python
PLAYBACK_KEYWORDS = ["show video", "play video", "playback", "vod", "continuous recording", "show recording"]
PLAYBACK_TIME_PATTERN = r"(\d{1,2}:\d{2})\s*(?:to|until|-|–)\s*(\d{1,2}:\d{2})"
```

**Recommendation:** Use Approach A with the upgraded Flash model. The model's JSON mode ensures structured output, and a single LLM call replaces both the regex hack and the separate SQL generation for playback queries (since playback queries don't need SQL — they need structured parameters for the Frigate VOD API).

**API Response Enhancement:**

Current `QueryResponse` (`api_models.py:10-18`):
```python
class QueryResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    explanation: str
    attempts: int
    error: str | None = None
```

Proposed addition:
```python
class PlaybackIntent(BaseModel):
    camera: str
    start_time: float    # Unix epoch seconds (UTC)
    end_time: float
    date: str            # YYYY-MM-DD

class QueryResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    explanation: str
    attempts: int
    error: str | None = None
    intent: str = "event_query"          # "event_query" | "playback_query" | "analytics_query"
    playback_intent: PlaybackIntent | None = None
```

**Feasibility:** Medium. Requires changes to:
- `api_models.py` — add `PlaybackIntent`, extend `QueryResponse`
- `api_controller.py` — add intent classification before SQL generation
- `avalai_gateway.py` — add `classify_intent` method
- `text_to_sql_use_case.py` — branch on intent type
- `api_presenter.py` — include `intent` and `playback_intent` in response

---

## 2. LLM Model Upgrade Analysis

### 2.1 Current Model Configuration

| Setting | File | Current Value |
|---------|------|---------------|
| `llm_model` (settings.py) | `config/settings.py:8` | `gemini-3.1-flash-lite` |
| `llm_model` (settings_model.py) | `domain/models/settings_model.py:6` | `gemini-3.1-flash-lite` |

The model is accessed via Avalai API (`https://api.avalai.ir/v1`) using the OpenAI-compatible SDK. This means any model name supported by Avalai can be used without changing the gateway code.

### 2.2 Upgrade Options

| Model | Context Window | Speed | SQL Accuracy | JSON Mode | Cost |
|-------|---------------|-------|-------------|-----------|------|
| `gemini-3.1-flash-lite` (current) | 1M tokens | Fastest | Good with heavy prompting | No | Lowest |
| `gemini-2.0-flash` | 1M tokens | Fast | Very good | Yes | Low |
| `gemini-2.5-flash` | 1M tokens | Fast | Excellent | Yes | Low-Medium |
| `gemini-1.5-flash` | 1M tokens | Medium | Good | Yes | Low |

**Recommended:** `gemini-2.5-flash` (or latest available 2.x Flash on Avalai). It supports native JSON mode (`response_format={"type": "json_object"}`), has better instruction adherence, and handles multi-step reasoning (intent classification + SQL generation) in a single call.

### 2.3 Impact on System Prompts & SQL Rules

**Current prompt structure** (`prompt_context.py:10-23`):
```
System prompt = Schema text + Sample queries (20 examples) + 20 SQL rules + Sub_label enrichment
```

The `SQL_RULES` string (`frigate_schema.py:132-153`) is **153 lines** of rules, many of which are workarounds for the lite model's poor instruction adherence:
- Rules 16-20 are entirely about `sub_label` disambiguation (5 rules for one concept)
- The `_enrich_question()` method (`text_to_sql_use_case.py:171-189`) appends hints to the user question because the lite model couldn't follow schema rules alone
- Rule 11 forces `id` column inclusion — a frontend workaround baked into LLM instructions

**With Flash upgrade:**

1. **Consolidate `sub_label` rules:** 5 rules → 1 rule. Flash models follow column semantics from schema descriptions without repeated emphasis.
2. **Remove `_enrich_question()`:** The method appends `NOTE: 'moein' is a person name...` to user questions. A Flash model can infer this from the schema description alone. This eliminates a code path and reduces prompt token usage.
3. **Simplify rule 11:** Instead of forcing the LLM to always include `id`, handle this in the presenter layer — if the query result has an `id` column, the frontend renders events; otherwise it renders a table.
4. **Enable JSON mode for intent classification:** The lite model doesn't support `response_format={"type": "json_object"}`, forcing regex-based SQL extraction (`_extract_sql()` at `text_to_sql_use_case.py:163-169`). Flash models can return structured JSON directly.

**Estimated prompt reduction:** ~40% fewer rules, ~30% fewer sample queries needed.

### 2.4 Migration Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Different SQL dialect preferences | Low — both models use SQLite syntax | Keep `SQLValidator` as safety net |
| Higher latency per call | Low — Flash is only ~100ms slower than Flash-Lite | Acceptable for chat UX |
| Cost increase | Low — Flash is ~2x Flash-Lite but still very cheap | Monitor usage via Avalai dashboard |
| JSON mode reliability | Very Low — Flash models have stable JSON mode | Add fallback regex parser |
| Existing test regressions | Medium — tests assert specific SQL patterns | Update tests to be pattern-based, not exact-match |

**Migration path:** Change `llm_model` in `settings.py` and `settings_model.py` from `gemini-3.1-flash-lite` to `gemini-2.5-flash`. No code changes needed in `AvalaiGateway` — it already passes `self._model` to the API.

---

## 3. GLM's Architectural Recommendations

### 3.1 Timestamp Calculations: Client-Side vs Backend LLM

**Recommendation: Hybrid approach — backend provides context, client performs conversion.**

**Rationale:**

The LLM should NOT perform timezone arithmetic. LLMs are unreliable at math, and timezone calculations involve DST rules, offset changes, and leap seconds. Instead:

1. **Backend injects timezone context into the LLM prompt:**
   ```
   ## Client Timezone Context
   - Client local time: 2026-07-21 21:40:00 (UTC+03:30, Asia/Tehran)
   - Server time: 2026-07-21 18:10:00 (UTC)
   - Offset: +03:30 (client is 3.5 hours ahead)
   - When user says "9:00 AM", they mean 9:00 AM Asia/Tehran = 05:30 UTC = Unix 1784377800
   ```

2. **LLM generates SQL with explicit Unix timestamp ranges:**
   ```sql
   SELECT id, label, camera, datetime(start_time, 'unixepoch', 'localtime') as start_time
   FROM event
   WHERE start_time BETWEEN 1784377800 AND 1784381400
   ORDER BY start_time DESC LIMIT 100;
   ```

3. **Client-side `TimeSyncNotifier` provides the offset** to the API call as a header or query parameter:
   ```dart
   // In ApiClient.query():
   final response = await _dio.post('/api/v1/query', data: {
     'question': question,
     'max_retries': maxRetries,
     'client_timezone': DateTime.now().timeZoneName,
     'client_offset_minutes': DateTime.now().timeZoneOffset.inMinutes,
     'client_timestamp': DateTime.now().millisecondsSinceEpoch ~/ 1000,
   });
   ```

4. **Backend `QueryRequest` model** receives and injects this into the prompt:
   ```python
   class QueryRequest(BaseModel):
       question: str
       max_retries: int = 3
       client_timezone: str | None = None
       client_offset_minutes: int | None = None
       client_timestamp: float | None = None
   ```

**Why not pure client-side?** The user says "9:00 AM" — the LLM needs to know what absolute time that refers to in order to generate `WHERE start_time BETWEEN ...`. If the client converts "9:00 AM" to Unix timestamps before sending, we lose the natural language aspect.

**Why not pure backend?** The backend doesn't know the user's timezone unless the client tells it. NTP-style skew detection requires comparing client clock to server clock.

### 3.2 Communicating `playback_intent` vs `event_intent` to Flutter

**Recommended: Extended `QueryResponse` with `intent` field.**

**Flow:**

```
User: "Show me video between 9:00 AM and 9:30 AM on cam1"
  ↓
Flutter sends: {question, client_offset_minutes: 210, client_timestamp: ...}
  ↓
Backend LLM classifies: {intent: "playback_query", camera: "cam1", start: 1784377800, end: 1784381400}
  ↓
Backend skips SQL generation for playback queries (no need to query recordings table)
  ↓
Backend returns: {intent: "playback_query", playback_intent: {camera, start_time, end_time, date}, explanation: "نمایش ویدیوی cam1 از 9:00 تا 9:30"}
  ↓
Flutter ChatBubble renders:
  - Explanation text (markdown)
  - "Open in Playback" button (deep link) → switches to NVR tab, selects cam1, sets date, seeks to 9:00 AM
  - Inline clip player (optional — plays the first segment)
```

**Deep Linking Mechanism:**

Since the app uses `MainScaffold` with `IndexedStack` and `ClassicNVRPage` with `TabBar`, we need a state-based navigation approach (not URL-based, since this is a mobile app):

```dart
// New provider: lib/presentation/providers/navigation_provider.dart
class NavigationState {
  final int mainTabIndex;        // 0=AI, 1=NVR, 2=Settings
  final int? nvrSubTabIndex;     // 0=Live, 1=Playback
  final PlaybackParams? playbackParams;  // camera, date, startTime, endTime
}

class NavigationNotifier extends Notifier<NavigationState> {
  void navigateToPlayback(PlaybackParams params) {
    state = NavigationState(
      mainTabIndex: 1,
      nvrSubTabIndex: 1,
      playbackParams: params,
    );
  }
}
```

`MainScaffold` watches `NavigationState` and switches tabs. `ClassicNVRPage` watches it and switches to Playback tab. `PlaybackTab` watches `playbackParams` and auto-selects camera/date/timeline.

**ChatBubble rendering for `playback_intent`:**

```dart
// In ChatBubble, after markdown text:
if (message.queryResult?['intent'] == 'playback_query') ...[
  const SizedBox(height: 12),
  _PlaybackDeepLinkButton(
    intent: PlaybackIntent.fromJson(message.queryResult!['playback_intent']),
    onTap: () => ref.read(navigationProvider.notifier).navigateToPlayback(params),
  ),
],
```

### 3.3 Creative Suggestions & Potential Pitfalls

#### Suggestion A: Unified "Smart Query" Pipeline

Instead of separate intent classification + SQL generation calls, use a **single LLM call** with structured output:

```python
def smart_query(self, question: str, schema_context: str, client_tz: dict) -> dict:
    response = self._client.chat.completions.create(
        model=self._model,
        messages=[
            {"role": "system", "content": f"{schema_context}\n\n{TIMEZONE_CONTEXT}"},
            {"role": "user", "content": question},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
```

Returns:
```json
{
  "intent": "playback_query",
  "sql": null,
  "playback": {"camera": "cam1", "start_time": 1784377800, "end_time": 1784381400},
  "explanation": "نمایش ویدیوی cam1 از 9:00 تا 9:30 صبح"
}
```

Or:
```json
{
  "intent": "event_query",
  "sql": "SELECT id, label, ... FROM event WHERE ...",
  "playback": null,
  "explanation": null
}
```

**Benefit:** One LLM call instead of two. The Flash model is smart enough to both classify intent and generate SQL in a single structured response.

#### Suggestion B: Proactive Time Sync Health Check

Add a periodic background timer in `TimeSyncNotifier` that checks skew every 5 minutes. If skew increases beyond 5 minutes, show a red banner with "Server clock may be drifting — timestamps may be inaccurate." This catches NTP failures on the server.

#### Suggestion C: Relative Time Resolution in LLM Context

Inject the current server time into every LLM prompt so relative time expressions ("yesterday", "last hour", "this morning") resolve correctly:

```
## Current Time Context
- Server UTC time: 2026-07-21 18:10:00 UTC (Unix: 1784394600)
- Client local time: 2026-07-21 21:40:00 +03:30
- "Today" for client = 2026-07-21 (Asia/Tehran)
- "Today" for server = 2026-07-21 (UTC)
- Start of client's today in UTC: 2026-07-20 20:30:00 (Unix: 1784340600)
```

This eliminates ambiguity when the user says "today at 9 AM" and the server's "today" starts at a different UTC midnight.

#### Pitfall 1: SQLite `localtime` vs Client Timezone

**Critical:** The SQL rules currently instruct the LLM to use `datetime(start_time, 'unixepoch', 'localtime')` for display. But `localtime` in SQLite uses the **server's** timezone (UTC), not the client's (Asia/Tehran). This means:

- User asks "What happened at 9 AM today?"
- LLM generates `WHERE strftime('%H', datetime(start_time, 'unixepoch', 'localtime')) = '09'`
- SQLite interprets `localtime` as UTC (server's TZ)
- Query matches events at 9:00 **UTC** = 12:30 **Asia/Tehran**

**Fix:** Either:
1. Set `TZ=Asia/Tehran` in the `frigate-intelligence` container environment, OR
2. Instruct the LLM to add the offset manually: `datetime(start_time, 'unixepoch', '+3 hours', '+30 minutes')`, OR
3. Have the backend convert client time to UTC Unix timestamps before injecting into the prompt

**Recommendation:** Option 3 is the most robust. The backend receives `client_offset_minutes=210` and generates prompt context like: "To filter for 9:00 AM client time, use `start_time >= <computed_unix_timestamp>`".

#### Pitfall 2: Playback Tab State Injection Race Condition

When the user taps "Open in Playback" from a chat message, the `NavigationNotifier` updates state, `MainScaffold` switches to NVR tab, `ClassicNVRPage` switches to Playback sub-tab, and `PlaybackTab` needs to load recordings for the specified camera/date/time. If `PlaybackTab` is already mounted (via `IndexedStack`), it needs to react to `playbackParams` changes in a `ref.listen()` callback, not in `build()`.

#### Pitfall 3: LLM JSON Mode Reliability

While Flash models support `response_format={"type": "json_object"}`, the output may occasionally be malformed. Always wrap JSON parsing in try/except and fall back to regex-based SQL extraction as a safety net.

#### Pitfall 4: Avalai API Model Availability

Before committing to a specific model name, verify that `gemini-2.5-flash` (or equivalent) is available on the Avalai API. The current gateway uses the OpenAI-compatible endpoint, so the model name must match Avalai's model list.

---

## 4. Actionable Step-by-Step Execution Plan

### Phase 12.1 — Time Synchronization Foundation (Backend)

**Estimated effort:** 2-3 hours

| Step | File | Action |
|------|------|--------|
| 1 | `frigate-intelligence/src/frigate_intelligence/interface_adapters/schemas/api_models.py` | Add `server_timestamp: float`, `server_timezone: str`, `server_datetime_iso: str` to `HealthResponse` |
| 2 | `frigate-intelligence/src/frigate_intelligence/interface_adapters/controllers/api_controller.py` | Update `health()` method to return current UTC timestamp and timezone info |
| 3 | `frigate-intelligence/src/frigate_intelligence/interface_adapters/schemas/api_models.py` | Add `client_timezone: str \| None`, `client_offset_minutes: int \| None`, `client_timestamp: float \| None` to `QueryRequest` |
| 4 | `frigate-intelligence/src/frigate_intelligence/use_cases/text_to_sql/text_to_sql_use_case.py` | Accept client timezone params in `execute()` and `execute_streaming()`, pass to prompt builder |
| 5 | `frigate-intelligence/src/frigate_intelligence/use_cases/text_to_sql/prompt_builder.py` | Accept `client_tz_info: dict` parameter, inject "Current Time Context" section into system prompt |
| 6 | `frigate-intelligence/src/frigate_intelligence/domain/value_objects/prompt_context.py` | Add `time_context: str` field, include in `as_system_prompt()` |
| 7 | `frigate-intelligence/tests/integration/test_api.py` | Update `test_health_endpoint` to assert new fields; add `test_query_with_timezone` |
| 8 | Deploy | `docker cp` updated files to `frigate-intelligence` container, restart |

### Phase 12.2 — Time Synchronization UI (Flutter Frontend)

**Estimated effort:** 2-3 hours

| Step | File | Action |
|------|------|--------|
| 1 | `frigate_app/lib/presentation/providers/time_sync_provider.dart` | **CREATE**: `TimeSyncNotifier` with periodic health check, skew calculation, `hasSignificantSkew` getter |
| 2 | `frigate_app/lib/data/datasources/api_client.dart` | Update `query()` to include `client_timezone`, `client_offset_minutes`, `client_timestamp` in POST body |
| 3 | `frigate_app/lib/presentation/pages/main_scaffold.dart` | Wrap `IndexedStack` in `Column` with conditional `MaterialBanner` for skew warning at top |
| 4 | `frigate_app/lib/main.dart` | Initialize `TimeSyncNotifier` on app startup (or use `ProviderScope` overrides) |
| 5 | `frigate_app/test/regression_test.dart` | Add test: `bug_023_time_sync_banner_shows_on_skew` — mock health response with skewed timestamp, verify banner appears |

### Phase 12.3 — LLM Model Upgrade

**Estimated effort:** 1-2 hours (mostly testing)

| Step | File | Action |
|------|------|--------|
| 1 | `frigate-intelligence/src/frigate_intelligence/config/settings.py` | Change `llm_model` default from `gemini-3.1-flash-lite` to `gemini-2.5-flash` |
| 2 | `frigate-intelligence/src/frigate_intelligence/domain/models/settings_model.py` | Change `llm_model` default to `gemini-2.5-flash` |
| 3 | `frigate-intelligence/src/frigate_intelligence/infrastructure/llm/avalai_gateway.py` | Add `classify_intent()` method using `response_format={"type": "json_object"}`; add `smart_query()` unified method |
| 4 | `frigate-intelligence/src/frigate_intelligence/domain/services/llm_service.py` | Add `classify_intent()` and `smart_query()` to `LLMService` protocol |
| 5 | `frigate-intelligence/src/frigate_intelligence/interface_adapters/schemas/frigate_schema.py` | Consolidate 20 SQL rules → ~12 rules; remove redundant `sub_label` rules (16-20 → 1 comprehensive rule); remove rule 11 (handle in presenter) |
| 6 | `frigate-intelligence/src/frigate_intelligence/use_cases/text_to_sql/text_to_sql_use_case.py` | Remove or simplify `_enrich_question()` — Flash model should follow schema rules without question enrichment |
| 7 | `frigate-intelligence/tests/unit/use_cases/test_text_to_sql_use_case.py` | Update tests: verify SQL generation with new model; test intent classification; ensure existing test patterns still pass |
| 8 | Deploy & verify | `docker cp` to container, restart, test with real queries via `curl` |

### Phase 12.4 — Intent Classification & Playback Deep Linking (Backend)

**Estimated effort:** 3-4 hours

| Step | File | Action |
|------|------|--------|
| 1 | `frigate-intelligence/src/frigate_intelligence/interface_adapters/schemas/api_models.py` | **ADD**: `PlaybackIntent` model (`camera`, `start_time`, `end_time`, `date`); add `intent: str` and `playback_intent: PlaybackIntent \| None` to `QueryResponse` |
| 2 | `frigate-intelligence/src/frigate_intelligence/use_cases/text_to_sql/text_to_sql_use_case.py` | Branch in `execute()`: if intent is `playback_query`, skip SQL generation, return `PlaybackIntent` directly; if `event_query`, proceed with existing SQL flow |
| 3 | `frigate-intelligence/src/frigate_intelligence/interface_adapters/presenters/api_presenter.py` | Update `to_query_response()` to include `intent` and `playback_intent` fields |
| 4 | `frigate-intelligence/src/frigate_intelligence/interface_adapters/controllers/api_controller.py` | Update `query()` and `query_stream()` to pass intent through to response |
| 5 | `frigate-intelligence/src/frigate_intelligence/infrastructure/llm/avalai_gateway.py` | Implement `smart_query()` — single LLM call that returns `{intent, sql, playback, explanation}` as JSON |
| 6 | `frigate-intelligence/tests/integration/test_api.py` | Add `test_query_playback_intent` — send "show video 9am to 9:30am cam1", verify response has `intent=playback_query` and `playback_intent` populated |
| 7 | Deploy | `docker cp` to container, restart |

### Phase 12.5 — Playback Deep Linking (Flutter Frontend)

**Estimated effort:** 3-4 hours

| Step | File | Action |
|------|------|--------|
| 1 | `frigate_app/lib/presentation/providers/navigation_provider.dart` | **CREATE**: `NavigationNotifier` with `NavigationState` (mainTabIndex, nvrSubTabIndex, playbackParams) |
| 2 | `frigate_app/lib/presentation/models/playback_params.dart` | **CREATE**: `PlaybackParams` data class (camera, date, startTime, endTime) with `fromJson()` factory |
| 3 | `frigate_app/lib/presentation/providers/chat_provider.dart` | Update `ChatMessage` to expose `intent` and `playbackIntent` from `queryResult` |
| 4 | `frigate_app/lib/presentation/widgets/chat_bubble.dart` | Add `_PlaybackDeepLinkButton` widget — renders when `intent == 'playback_query'`, shows "Open in Playback" button with camera/time info |
| 5 | `frigate_app/lib/presentation/pages/main_scaffold.dart` | Watch `NavigationState` — when `mainTabIndex` changes externally, update `_currentIndex` |
| 6 | `frigate_app/lib/presentation/pages/classic_nvr_page.dart` | Watch `NavigationState` — when `nvrSubTabIndex` changes, switch `TabController` index |
| 7 | `frigate_app/lib/presentation/pages/playback_tab.dart` | Watch `playbackParams` from `NavigationState` — when set, auto-select camera, set date, fetch recordings, seek to start time |
| 8 | `frigate_app/test/regression_test.dart` | Add test: `bug_024_playback_deep_link_navigates` — simulate playback intent, verify NavigationState updates |

### Phase 12.6 — Inline Clip Playback for VOD Ranges

**Estimated effort:** 2 hours

| Step | File | Action |
|------|------|--------|
| 1 | `frigate_app/lib/presentation/widgets/inline_vod_player.dart` | **CREATE**: Widget that takes `camera`, `startTime`, `endTime`, constructs Frigate clip.mp4 URL, plays via `media_kit` |
| 2 | `frigate_app/lib/presentation/widgets/chat_bubble.dart` | For `playback_query` intent, optionally render `InlineVodPlayer` below the deep link button (plays first 10-second segment) |
| 3 | `frigate_app/lib/data/datasources/api_client.dart` | Add `getVodClipUrl(camera, startTime, endTime)` helper that constructs `http://{ip}:5000/api/{camera}/start/{ts}/end/{ts}/clip.mp4` |

### Phase 12.7 — Integration Testing & Deployment

**Estimated effort:** 2 hours

| Step | Command | Action |
|------|---------|--------|
| 1 | `cd frigate-intelligence && python -m pytest tests/ -v` | Run all backend tests, verify count ≥ baseline |
| 2 | `cd frigate-intelligence && ruff check src/ tests/` | Lint check |
| 3 | `cd frigate_app && flutter analyze` | Static analysis — must be 0 issues |
| 4 | `cd frigate_app && flutter test` | All tests pass |
| 5 | `cd frigate_app && flutter build apk --debug` | Build succeeds |
| 6 | Manual test on device | Test queries: "Show me video 9am to 9:30am on cam1", "Was moein seen today?", "What happened last hour?" |
| 7 | `BUG_FIXING_DISCIPLINE.md` | Update Bug Registry with Phase 12 entries |

---

## Summary: Effort & Dependency Graph

```
Phase 12.1 (Backend Time Sync) ──┬── Phase 12.2 (Flutter Time Sync UI)
                                  │
Phase 12.3 (LLM Model Upgrade) ──┼── Phase 12.4 (Intent Classification Backend)
                                  │        │
                                  │        └── Phase 12.5 (Playback Deep Linking Flutter)
                                  │                 │
                                  │                 └── Phase 12.6 (Inline VOD Player)
                                  │
                                  └── Phase 12.7 (Integration Testing)
```

**Total estimated effort:** 15-20 hours  
**Risk level:** Medium (LLM behavior change + new navigation pattern)  
**Rollback plan:** Revert `llm_model` to `gemini-3.1-flash-lite` and remove `intent` field from `QueryResponse` — all existing functionality continues to work since `intent` defaults to `"event_query"`.

---

## 5. BUG_FIXING_DISCIPLINE.md Compliance

This section ensures all Phase 12 work adheres to the project's bug-fixing discipline.

### 5.1 Pre-Implementation Baseline (§1 — Regression-First)

Before starting any Phase 12 work, record the baseline:

```bash
# Backend baseline
cd frigate-intelligence
python -m pytest tests/ --co -q | wc -l    # Record test count (baseline)
python -m pytest tests/ -v --tb=short       # Must be all green

# Frontend baseline
cd frigate_app
flutter test --reporter compact 2>&1 | tail -1   # Record pass/fail summary
flutter analyze                                   # Must be 0 issues
```

**Rule:** Test count must never decrease. Every phase that modifies code must add ≥1 regression test.

### 5.2 Reproduction Before Fixing (§2)

Phase 12 introduces features, not bug fixes. However, the timezone issue (Pitfall 1: SQLite `localtime` = UTC, not client TZ) is a latent bug. Reproduction steps:

```bash
# Reproduce: query "what happened at 9am today" — verify SQL uses localtime (UTC) not client TZ
curl -s -X POST http://192.168.85.203:8088/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What happened at 9am today?"}' | python -m json.tool

# Check: the generated SQL will use strftime('%H', datetime(start_time, 'unixepoch', 'localtime')) = '09'
# This matches 9:00 UTC = 12:30 Asia/Tehran, NOT 9:00 client local time
```

**Environment:**
- Server: `192.168.85.203:8088` (frigate-intelligence)
- Frigate: `192.168.85.203:5000`
- Device: `R5CY23R9DXR` (Samsung SM-S938B, Android 16)
- Container timezone: UTC (no `TZ` env var)

### 5.3 Regression Test Plan (§3 — Naming Convention)

Every phase must include regression tests following the naming convention:

| Phase | BUG ID | Test Name | Location | Description |
|-------|--------|-----------|----------|-------------|
| 12.1 | BUG-023 | `test_bug_023_health_endpoint_returns_timestamp` | `tests/integration/test_api.py` | Health response includes `server_timestamp`, `server_timezone`, `server_datetime_iso` |
| 12.1 | BUG-023 | `test_bug_023_query_accepts_client_timezone` | `tests/integration/test_api.py` | Query endpoint accepts `client_offset_minutes` and includes it in prompt context |
| 12.2 | BUG-024 | `bug_024_time_sync_banner_shows_on_skew` | `frigate_app/test/regression_test.dart` | TimeSyncNotifier detects skew > 2 min and banner renders in MainScaffold |
| 12.2 | BUG-024 | `bug_024_time_sync_no_banner_when_synced` | `frigate_app/test/regression_test.dart` | No banner when skew < 2 min |
| 12.3 | BUG-025 | `test_bug_025_llm_model_upgrade_sql_generation` | `tests/unit/use_cases/test_text_to_sql_use_case.py` | SQL generation still produces valid SELECT queries with new model |
| 12.3 | BUG-025 | `test_bug_025_enrich_question_removed` | `tests/unit/use_cases/test_text_to_sql_use_case.py` | Verify `_enrich_question()` is removed or simplified; Flash model follows schema rules |
| 12.4 | BUG-026 | `test_bug_026_playback_intent_classification` | `tests/integration/test_api.py` | "Show video 9am-9:30am cam1" returns `intent=playback_query` with `PlaybackIntent` |
| 12.4 | BUG-026 | `test_bug_026_event_intent_still_works` | `tests/integration/test_api.py` | "Was moein seen today?" returns `intent=event_query` with SQL rows |
| 12.5 | BUG-027 | `bug_027_playback_deep_link_navigates` | `frigate_app/test/regression_test.dart` | Tapping "Open in Playback" switches MainScaffold to NVR tab and Playback sub-tab |
| 12.5 | BUG-027 | `bug_027_playback_params_auto_select_camera` | `frigate_app/test/regression_test.dart` | PlaybackTab auto-selects camera and date from `PlaybackParams` |
| 12.6 | BUG-028 | `bug_028_inline_vod_player_constructs_url` | `frigate_app/test/regression_test.dart` | InlineVodPlayer constructs correct clip.mp4 URL from camera + timestamps |

### 5.4 No Silent Failures (§5)

All new code must follow the logging conventions:

| Component | Prefix | Example |
|-----------|--------|---------|
| Time sync | `[TimeSync]` | `[TimeSync] Skew detected: 210 minutes (client ahead)` |
| Intent classification | `[Intent]` | `[Intent] Classified as playback_query for cam1` |
| Navigation | `[Nav]` | `[Nav] Deep-linking to Playback: cam1, 2026-07-21, 09:00-09:30` |
| VOD player | `[VOD]` | `[VOD] Opening URL: http://192.168.85.203:5000/api/cam1/start/.../clip.mp4` |

**Error handling requirements:**
- `TimeSyncNotifier`: if health() fails, log `[TimeSync] Health check failed: $e` and set `error` state (don't silently ignore)
- `classify_intent()`: if JSON parsing fails, log `[Intent] LLM JSON parse failed: $raw`, fall back to regex intent detection
- `NavigationNotifier`: if `PlaybackParams` are invalid, log `[Nav] Invalid playback params: $params` and abort navigation
- `InlineVodPlayer`: if media_kit fails to open, log `[VOD] Failed to open: $e` and show error widget

### 5.5 Deployment Gate (§6)

Before merging any Phase 12 work, ALL checks must pass:

| Check | Command | Required Result |
|-------|---------|-----------------|
| Backend lint | `ruff check src/ tests/` | 0 errors |
| Backend tests | `python -m pytest tests/ -v` | All pass, count ≥ baseline + 8 (new tests) |
| Flutter analyze | `flutter analyze` | 0 issues |
| Flutter tests | `flutter test` | All pass, count ≥ 4 + 6 (new tests) |
| Flutter build | `flutter build apk --debug` | Success |
| Frigate API | `curl -s http://192.168.85.203:5000/api/config` | 200 OK |
| Backend API | `curl -s http://192.168.85.203:8088/api/v1/health` | 200 OK with `server_timestamp` |
| RTSP port | `Test-NetConnection 192.168.85.203 -Port 8554` | True |
| Time sync | `curl -s http://192.168.85.203:8088/api/v1/health \| python -m json.tool` | `server_timestamp` within 60s of local clock |

**If any check fails, deployment is blocked.**

### 5.6 Bug Registry Pre-Assignment (§7)

The following entries will be added to the Bug Registry in `BUG_FIXING_DISCIPLINE.md` upon completion of each phase:

| ID | Phase | Description | Status |
|----|-------|-------------|--------|
| BUG-023 | 12.1/12.2 | Server health endpoint lacks timestamp/timezone; client cannot detect clock skew | Open |
| BUG-024 | 12.1/12.2 | SQLite `localtime` uses server UTC, not client timezone — time-based queries return wrong results | Open |
| BUG-025 | 12.3 | LLM model `gemini-3.1-flash-lite` lacks JSON mode and requires heavy prompt enrichment hacks | Open |
| BUG-026 | 12.4 | No intent classification — LLM cannot distinguish event queries from playback/VOD requests | Open |
| BUG-027 | 12.5 | No deep-linking from chat to Playback tab — user cannot navigate to VOD from LLM response | Open |
| BUG-028 | 12.6 | No inline VOD clip playback in chat — user must manually navigate to Playback tab | Open |

Each entry will be updated with Root Cause, Fix, Regression Test, and Status=Fixed upon phase completion.
