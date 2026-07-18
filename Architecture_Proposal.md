# Frigate Intelligence Platform — Architecture Proposal

## 1. Architecture Analysis

### 1.1 Why Clean Architecture?

This system has **multiple input channels** (CLI, Flutter, Telegram, Bale), **multiple external dependencies** (Frigate DB, Avalai LLM API, POS API), and **multiple output formats** (text, images, notifications). Clean Architecture ensures:

- **Domain logic is isolated** — business rules (text-to-SQL, event correlation, alert logic) don't depend on Frigate, LangChain, or Telegram.
- **Swappable infrastructure** — Avalai API can be replaced with any OpenAI-compatible endpoint. SQLite can be swapped for PostgreSQL. Bots can be added/removed without touching core logic.
- **Testable core** — Use cases can be unit-tested with mock gateways, no real DB or LLM needed.
- **Independent client evolution** — Flutter app, CLI, and bots can be developed independently against the same API.

### 1.2 Layer Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│  Frameworks & Drivers (Outermost)                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐   │
│  │ FastAPI  │  │ CLI      │  │ Telegram │  │ Bale Bot      │   │
│  │ (REST)   │  │ (Typer)  │  │ Bot      │  │               │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬───────┘   │
│       │              │              │                │           │
│  ┌────┴──────────────┴──────────────┴────────────────┴───────┐  │
│  │              Interface Adapters                           │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ Control- │  │ Frigate  │  │ LLM      │  │ POS      │  │  │
│  │  │ lers     │  │ DB       │  │ Gateway  │  │ Gateway  │  │  │
│  │  │ (API     │  │ Gateway  │  │ (Avalai) │  │          │  │  │
│  │  │  routes) │  │ (SQLite) │  │          │  │          │  │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │  │
│  └───────┼─────────────┼─────────────┼─────────────┼────────┘  │
│          │             │             │             │            │
│  ┌───────┴─────────────┴─────────────┴─────────────┴────────┐  │
│  │                    Use Cases                             │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │ TextToSQL  │  │ EventQuery │  │ NotificationSender │  │  │
│  │  │ UseCase    │  │ UseCase    │  │ UseCase            │  │  │
│  │  └─────┬──────┘  └─────┬──────┘  └─────────┬──────────┘  │  │
│  └────────┼───────────────┼───────────────────┼─────────────┘  │
│           │               │                   │                │
│  ┌────────┴───────────────┴───────────────────┴─────────────┐  │
│  │                    Domain (Core)                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │ Entities │  │ Repos    │  │ LLM      │  │ Notifier  │ │  │
│  │  │ (Event,  │  │ Inter-   │  │ Inter-   │  │ Inter-    │ │  │
│  │  │  Record, │  │ faces    │  │ faces    │  │ faces     │ │  │
│  │  │  Query)  │  │          │  │          │  │           │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Module Placement

| Module | Layer | Rationale |
|--------|-------|-----------|
| **LangChain / ReAct logic** | Use Cases | Orchestration of LLM calls is a use case. The ReAct loop, prompt construction, and SQL execution are business logic. |
| **Avalai API (OpenAI-compatible)** | Frameworks & Drivers → Gateway | External API call. Gateway implements `LLMInterface` from Domain. |
| **Frigate SQLite DB** | Frameworks & Drivers → Gateway | Database access. Gateway implements `FrigateRepository` interface from Domain. |
| **Telegram / Bale Bots** | Frameworks & Drivers | Delivery channels. They call Use Cases via Controllers. |
| **FastAPI REST API** | Interface Adapters → Controllers | HTTP endpoints for Flutter/external clients. |
| **POS API** | Frameworks & Drivers → Gateway | External hardware integration. Implements `POSInterface` from Domain. |
| **Frigate Schema (DB context)** | Use Cases | Schema is injected as context into LLM prompts. It's configuration data, not infrastructure. |

### 1.4 Dependency Rule

**Dependencies point inward only.** Domain knows nothing about LangChain, SQLite, or Telegram. Use Cases know about Domain interfaces only. Gateways implement Domain interfaces. Controllers call Use Cases.

---

## 2. Directory Structure

```
frigate-intelligence/
│
├── pyproject.toml                    # Poetry/uv project config
├── README.md
├── .env.example                      # AVALAI_API_KEY, FRIGATE_DB_PATH, TELEGRAM_TOKEN, etc.
│
├── src/
│   └── frigate_intelligence/
│       │
│       ├── domain/                           # ── CORE: Pure Python, no external deps ──
│       │   ├── __init__.py
│       │   ├── entities/
│       │   │   ├── __init__.py
│       │   │   ├── event.py                  # Event dataclass (id, label, camera, start_time, ...)
│       │   │   ├── recording.py              # Recording dataclass
│       │   │   ├── timeline_entry.py         # Timeline dataclass
│       │   │   ├── review_segment.py         # ReviewSegment dataclass
│       │   │   ├── query_result.py           # QueryResult dataclass (sql, rows, columns, error)
│       │   │   └── notification.py           # Notification dataclass (message, image_path, chat_id)
│       │   │
│       │   ├── repositories/                 # Abstract interfaces (Protocol/ABC)
│       │   │   ├── __init__.py
│       │   │   ├── frigate_repository.py     # Protocol: get_events, get_recordings, execute_sql
│       │   │   └── pos_repository.py         # Protocol: get_transaction_by_time
│       │   │
│       │   ├── services/                     # Abstract service interfaces
│       │   │   ├── __init__.py
│       │   │   ├── llm_service.py            # Protocol: generate_sql, explain_result, chat
│       │   │   └── notifier_service.py       # Protocol: send_notification, send_image
│       │   │
│       │   └── value_objects/
│       │       ├── __init__.py
│       │       ├── sql_query.py              # SQLQuery (validated SQL string)
│       │       ├── prompt_context.py         # PromptContext (schema, samples, user_question)
│       │       └── time_range.py             # TimeRange (start, end as unix timestamps)
│       │
│       ├── use_cases/                        # ── Application Business Rules ──
│       │   ├── __init__.py
│       │   ├── text_to_sql/
│       │   │   ├── __init__.py
│       │   │   ├── text_to_sql_use_case.py   # ReAct loop: question → SQL → execute → answer
│       │   │   ├── sql_validator.py          # Validate SQL (SELECT only, no DROP/DELETE)
│       │   │   └── prompt_builder.py         # Build system prompt with schema context
│       │   │
│       │   ├── query_events/
│       │   │   ├── __init__.py
│       │   │   └── query_events_use_case.py  # Direct event queries (no LLM)
│       │   │
│       │   ├── correlate_pos/
│       │   │   ├── __init__.py
│       │   │   └── correlate_pos_use_case.py # Match POS transaction time with camera events
│       │   │
│       │   └── send_notification/
│       │       ├── __init__.py
│       │       └── send_notification_use_case.py
│       │
│       ├── interface_adapters/               # ── Interface Adapters ──
│       │   ├── __init__.py
│       │   ├── controllers/
│       │   │   ├── __init__.py
│       │   │   ├── api_controller.py         # FastAPI route handlers
│       │   │   ├── cli_controller.py         # CLI command handlers (Typer)
│       │   │   └── bot_controller.py         # Telegram/Bale message handlers
│       │   │
│       │   ├── presenters/
│       │   │   ├── __init__.py
│       │   │   ├── cli_presenter.py          # Format output for terminal (tables, colors)
│       │   │   ├── api_presenter.py          # Format output as JSON for REST
│       │   │   └── bot_presenter.py          # Format output for Telegram/Bale (markdown)
│       │   │
│       │   └── schemas/
│       │       ├── __init__.py
│       │       ├── frigate_schema.py         # Frigate DB schema as structured context
│       │       └── api_models.py             # Pydantic models for API request/response
│       │
│       ├── infrastructure/                   # ── Frameworks & Drivers ──
│       │   ├── __init__.py
│       │   ├── database/
│       │   │   ├── __init__.py
│       │   │   ├── frigate_sqlite_gateway.py # Implements FrigateRepository (SQLite)
│       │   │   └── connection.py             # SQLite connection factory
│       │   │
│       │   ├── llm/
│       │   │   ├── __init__.py
│       │   │   ├── avalai_gateway.py         # Implements LLMService (OpenAI-compatible)
│       │   │   └── langchain_react_agent.py  # LangChain ReAct agent wrapper
│       │   │
│       │   ├── pos/
│       │   │   ├── __init__.py
│       │   │   └── pos_api_gateway.py        # Implements POSRepository (HTTP API)
│       │   │
│       │   ├── notifiers/
│       │   │   ├── __init__.py
│       │   │   ├── telegram_notifier.py      # Implements NotifierService (Telegram)
│       │   │   └── bale_notifier.py          # Implements NotifierService (Bale)
│       │   │
│       │   ├── api/
│       │   │   ├── __init__.py
│       │   │   ├── fastapi_app.py            # FastAPI app factory
│       │   │   └── routes/
│       │   │       ├── __init__.py
│       │   │       ├── query_routes.py       # /api/v1/query (text-to-SQL)
│       │   │       ├── event_routes.py       # /api/v1/events
│       │   │       └── health_routes.py      # /api/v1/health
│       │   │
│       │   └── cli/
│       │       ├── __init__.py
│       │       └── cli_app.py                # Typer CLI app factory
│       │
│       ├── config/                           # ── Configuration & Composition Root ──
│       │   ├── __init__.py
│       │   ├── settings.py                   # Pydantic Settings (env vars)
│       │   └── dependencies.py               # Dependency injection container
│       │
│       └── main.py                           # Entry point (assembles everything)
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── test_event.py
│   │   │   └── test_sql_query.py
│   │   ├── use_cases/
│   │   │   ├── test_text_to_sql_use_case.py  # Mock LLM + Mock Repository
│   │   │   └── test_sql_validator.py
│   │   └── interface_adapters/
│   │       └── test_prompt_builder.py
│   ├── integration/
│   │   ├── test_frigate_sqlite_gateway.py    # Real SQLite (test DB)
│   │   └── test_avalai_gateway.py            # Real Avalai API (marked, skipped in CI)
│   └── e2e/
│       └── test_cli_text_to_sql.py           # Full CLI flow
│
└── docs/
    ├── Frigate_Database_Schema_Report.md     # Already created
    └── architecture.md                       # This document
```

---

## 3. Roadmap

### Phase 1: Core Text-to-SQL (CLI) — *Immediate*

**Goal**: User types a natural language question in CLI → LLM generates SQL → executes on Frigate DB → returns formatted result.

| Step | Task | Layer | Details |
|------|------|-------|---------|
| 1.1 | Project scaffolding | — | `pyproject.toml`, directory structure, dependencies (typer, openai, pydantic, rich) |
| 1.2 | Domain entities | Domain | `Event`, `QueryResult`, `SQLQuery`, `PromptContext` dataclasses |
| 1.3 | Repository interface | Domain | `FrigateRepository` Protocol: `execute_sql(sql) → QueryResult` |
| 1.4 | LLM service interface | Domain | `LLMService` Protocol: `generate_sql(question, schema_context) → SQLQuery` |
| 1.5 | Frigate SQLite Gateway | Infrastructure | Implements `FrigateRepository` with `sqlite3`, connects to `/opt/frigate/config/frigate.db` |
| 1.6 | Avalai LLM Gateway | Infrastructure | Implements `LLMService` using `openai` package with `base_url="https://avalai.ir/v1"`, `api_key` from env |
| 1.7 | Prompt Builder | Use Cases | Builds system prompt with Frigate schema, sample data, SQL rules (SELECT only) |
| 1.8 | SQL Validator | Use Cases | Rejects non-SELECT statements, validates table/column names against schema |
| 1.9 | Text-to-SQL Use Case | Use Cases | ReAct loop: question → LLM → SQL → validate → execute → format → answer. If error, feed back to LLM for retry (max 3) |
| 1.10 | CLI Controller + Presenter | Interface Adapters | Typer CLI with `rich` table output. Command: `frigate-ai query "آخرین رویدادهای person"` |
| 1.11 | Composition Root | Config | `main.py` wires dependencies: SQLite gateway, Avalai gateway, use case, CLI controller |
| 1.12 | Unit tests | Tests | Mock LLM + Mock Repository, test use case logic, SQL validator, prompt builder |
| 1.13 | Integration test | Tests | Connect to real Frigate DB, run sample queries |

**Deliverable**: Working CLI tool that answers natural language questions about Frigate events.

### Phase 2: REST API (FastAPI) — *Next*

**Goal**: Expose the same use cases via REST API for Flutter app.

| Step | Task | Details |
|------|------|---------|
| 2.1 | FastAPI app factory | `fastapi_app.py` with CORS, error handling |
| 2.2 | API routes | `POST /api/v1/query` (text-to-SQL), `GET /api/v1/events` (direct query) |
| 2.3 | Pydantic models | Request/response schemas for API |
| 2.4 | API presenter | Format QueryResult as JSON response |
| 2.5 | Auth middleware | API key or JWT for Flutter client |
| 2.6 | Docker deployment | Dockerfile + docker-compose for backend service |

**Deliverable**: REST API running alongside Frigate, accessible from Flutter.

### Phase 3: Messaging Bot Integration — *Short-term*

**Goal**: Telegram and Bale bots that answer queries and send alerts.

| Step | Task | Details |
|------|------|---------|
| 3.1 | Bot controller | Unified message handler for Telegram + Bale |
| 3.2 | Telegram notifier | `python-telegram-bot` integration |
| 3.3 | Bale notifier | Bale API integration |
| 3.4 | Notification use case | Trigger alerts on new events (webhook from Frigate or polling) |
| 3.5 | Bot presenter | Format results as Telegram markdown with inline images |

**Deliverable**: Bots that respond to natural language queries and send event alerts.

### Phase 4: Flutter Client — *Medium-term*

**Goal**: Mobile + desktop app with voice input and image display.

| Step | Task | Details |
|------|------|---------|
| 4.1 | Flutter project scaffold | Flutter app with Clean Architecture (mirroring backend layers) |
| 4.2 | API client | Dio/HTTP client for FastAPI endpoints |
| 4.3 | Chat UI | Chat interface for text-to-SQL queries |
| 4.4 | Voice input | `speech_to_text` plugin → send transcript to API |
| 4.5 | Image display | Fetch event thumbnails/snapshots from Frigate API |
| 4.6 | Push notifications | FCM for Android, APNs for iOS |

**Deliverable**: Flutter app with chat, voice, and image features.

### Phase 5: POS Integration & Advanced Features — *Long-term*

**Goal**: Correlate POS transactions with camera events, advanced analytics.

| Step | Task | Details |
|------|------|---------|
| 5.1 | POS API gateway | HTTP client for POS device API |
| 5.2 | Correlate POS use case | Match transaction timestamp with camera events ±time window |
| 5.3 | Event replay | Fetch video clip for matched event, send to Flutter/bot |
| 5.4 | Analytics dashboard | Aggregate queries (hourly traffic, peak times, etc.) |
| 5.5 | Multi-camera support | Extend schema context for multiple cameras |
| 5.6 | gRPC endpoint | Optional gRPC for high-performance Flutter communication |

**Deliverable**: Full platform with POS correlation and analytics.

---

## 4. Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.12+ | Matches Frigate ecosystem, LangChain support |
| Package Manager | `uv` or Poetry | Fast, reproducible dependencies |
| CLI Framework | Typer + Rich | Beautiful CLI with minimal code |
| Web Framework | FastAPI | Async, OpenAPI docs, Pydantic validation |
| LLM Orchestration | LangChain (ReAct agent) | Standard for LLM agent patterns |
| LLM API Client | `openai` package | Compatible with Avalai.ir (OpenAI-compatible) |
| Database | sqlite3 (stdlib) | Direct access to Frigate DB |
| Settings | pydantic-settings | Type-safe env var management |
| Testing | pytest + pytest-asyncio | Standard Python testing |
| Bot Framework | python-telegram-bot | Mature Telegram library |
| Flutter | Flutter + Dio | Cross-platform, REST client |

---

## 5. Dependency Injection Pattern

```python
# src/frigate_intelligence/config/dependencies.py

from dataclasses import dataclass
from frigate_intelligence.domain.repositories.frigate_repository import FrigateRepository
from frigate_intelligence.domain.services.llm_service import LLMService
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import TextToSQLUseCase
from frigate_intelligence.infrastructure.database.frigate_sqlite_gateway import FrigateSqliteGateway
from frigate_intelligence.infrastructure.llm.avalai_gateway import AvalaiGateway
from frigate_intelligence.config.settings import Settings


@dataclass
class Container:
    frigate_repo: FrigateRepository
    llm_service: LLMService
    text_to_sql_use_case: TextToSQLUseCase


def create_container(settings: Settings) -> Container:
    frigate_repo = FrigateSqliteGateway(db_path=settings.frigate_db_path)
    llm_service = AvalaiGateway(
        api_key=settings.avalai_api_key,
        base_url=settings.avalai_base_url,
        model=settings.llm_model,
    )
    text_to_sql = TextToSQLUseCase(
        frigate_repo=frigate_repo,
        llm_service=llm_service,
        schema_context=settings.frigate_schema_context,
    )
    return Container(
        frigate_repo=frigate_repo,
        llm_service=llm_service,
        text_to_sql_use_case=text_to_sql,
    )
```

---

## 6. ReAct Agent Flow (Phase 1)

```
User: "آخرین بار کی شخصی جلوی دوربین بود؟"
                    │
                    ▼
        ┌───────────────────────┐
        │   Prompt Builder      │  Injects: Frigate schema, sample data, SQL rules
        │   (System Prompt)     │  "You are a SQL expert. Use only SELECT statements."
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   LLM (Avalai/Gemini) │  Thought: "User wants latest person event"
        │   ReAct Step 1        │  Action: generate SQL
        │                       │  SQL: SELECT MAX(start_time) FROM event WHERE label='person'
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   SQL Validator       │  ✓ SELECT only
        │                       │  ✓ Valid table/column names
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   Frigate Repository  │  Executes SQL on SQLite
        │   (execute_sql)       │  Returns: [(1784386154.72,)]
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   LLM (Avalai/Gemini) │  Observation: "1784386154.72"
        │   ReAct Step 2        │  Thought: "This is a Unix timestamp"
        │                       │  Answer: "آخرین بار شخصی در ساعت 14:49:14 امروز جلوی دوربین بود"
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   CLI Presenter       │  Rich table output in terminal
        └───────────────────────┘
```

---

## 7. Key Design Decisions

1. **LangChain in Use Cases, not Infrastructure**: The ReAct agent orchestration is business logic. The `langchain_react_agent.py` in infrastructure is a thin wrapper; the actual prompt construction and retry logic lives in `TextToSQLUseCase`.

2. **Schema as configuration, not code**: `Frigate_Database_Schema_Report.md` content is loaded as a string and injected into prompts. It's defined in `config/settings.py` and can be updated without code changes.

3. **SQL safety**: `SQLValidator` enforces SELECT-only, validates table names against a whitelist, and limits result rows (default 100).

4. **Gateway pattern for Avalai**: `AvalaiGateway` implements `LLMService` Protocol. If Avalai changes or we switch to direct Google API, only this file changes.

5. **Presenter pattern**: Same Use Case output can be rendered as Rich table (CLI), JSON (API), or Telegram markdown (Bot) — no logic duplication.

6. **Composition Root in `main.py`**: All wiring happens in one place. Easy to swap implementations for testing.
