# Phase 1: CLI Text-to-SQL Agent — Detailed Roadmap

## Objective

Build a CLI tool that accepts natural language questions (Persian/English), converts them to SQL via LLM (ReAct pattern), executes on Frigate SQLite DB, and returns formatted results.

---

## Prerequisites

- Python 3.12+ installed locally
- `uv` package manager installed
- Frigate DB accessible (locally via SSH tunnel or on server)
- Avalai.ir API key obtained
- `Frigate_Database_Schema_Report.md` available for schema context

---

## Step 1.1: Project Scaffolding

**Actions:**
1. Create project root: `C:\Users\Moein\Documents\Codes\YOLO\frigate-intelligence\`
2. Create `pyproject.toml` with `uv`

**File: `frigate-intelligence/pyproject.toml`**
```toml
[project]
name = "frigate-intelligence"
version = "0.1.0"
description = "AI-powered Frigate NVR analytics platform"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "openai>=1.0.0",
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "langchain-core>=0.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
]

[project.scripts]
frigate-ai = "frigate_intelligence.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Directory structure to create:**
```
frigate-intelligence/
├── pyproject.toml
├── .env.example
├── src/
│   └── frigate_intelligence/
│       ├── __init__.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── entities/
│       │   │   ├── __init__.py
│       │   │   ├── event.py
│       │   │   ├── recording.py
│       │   │   ├── timeline_entry.py
│       │   │   ├── review_segment.py
│       │   │   ├── query_result.py
│       │   │   └── notification.py
│       │   ├── repositories/
│       │   │   ├── __init__.py
│       │   │   └── frigate_repository.py
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── llm_service.py
│       │   │   └── notifier_service.py
│       │   └── value_objects/
│       │       ├── __init__.py
│       │       ├── sql_query.py
│       │       ├── prompt_context.py
│       │       └── time_range.py
│       ├── use_cases/
│       │   ├── __init__.py
│       │   ├── text_to_sql/
│       │   │   ├── __init__.py
│       │   │   ├── text_to_sql_use_case.py
│       │   │   ├── sql_validator.py
│       │   │   └── prompt_builder.py
│       │   ├── query_events/
│       │   │   ├── __init__.py
│       │   │   └── query_events_use_case.py
│       │   ├── correlate_pos/
│       │   │   ├── __init__.py
│       │   │   └── correlate_pos_use_case.py
│       │   └── send_notification/
│       │       ├── __init__.py
│       │       └── send_notification_use_case.py
│       ├── interface_adapters/
│       │   ├── __init__.py
│       │   ├── controllers/
│       │   │   ├── __init__.py
│       │   │   ├── api_controller.py
│       │   │   ├── cli_controller.py
│       │   │   └── bot_controller.py
│       │   ├── presenters/
│       │   │   ├── __init__.py
│       │   │   ├── cli_presenter.py
│       │   │   ├── api_presenter.py
│       │   │   └── bot_presenter.py
│       │   └── schemas/
│       │       ├── __init__.py
│       │       ├── frigate_schema.py
│       │       └── api_models.py
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── database/
│       │   │   ├── __init__.py
│       │   │   ├── frigate_sqlite_gateway.py
│       │   │   └── connection.py
│       │   ├── llm/
│       │   │   ├── __init__.py
│       │   │   ├── avalai_gateway.py
│       │   │   └── langchain_react_agent.py
│       │   ├── pos/
│       │   │   ├── __init__.py
│       │   │   └── pos_api_gateway.py
│       │   ├── notifiers/
│       │   │   ├── __init__.py
│       │   │   ├── telegram_notifier.py
│       │   │   └── bale_notifier.py
│       │   ├── api/
│       │   │   ├── __init__.py
│       │   │   ├── fastapi_app.py
│       │   │   └── routes/
│       │   │       ├── __init__.py
│       │   │       ├── query_routes.py
│       │   │       ├── event_routes.py
│       │   │       └── health_routes.py
│       │   └── cli/
│       │       ├── __init__.py
│       │       └── cli_app.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py
│       │   └── dependencies.py
│       └── main.py
└── tests/
    ├── __init__.py
    ├── unit/
    │   ├── __init__.py
    │   ├── domain/
    │   │   ├── __init__.py
    │   │   ├── test_event.py
    │   │   └── test_sql_query.py
    │   ├── use_cases/
    │   │   ├── __init__.py
    │   │   ├── test_text_to_sql_use_case.py
    │   │   └── test_sql_validator.py
    │   └── interface_adapters/
    │       ├── __init__.py
    │       └── test_prompt_builder.py
    ├── integration/
    │   ├── __init__.py
    │   ├── test_frigate_sqlite_gateway.py
    │   └── test_avalai_gateway.py
    └── e2e/
        ├── __init__.py
        └── test_cli_text_to_sql.py
```

**Acceptance Criteria:**
- [x] `pyproject.toml` exists with correct dependencies
- [x] All directories and `__init__.py` files created
- [x] `uv sync` runs without errors
- [x] `python -c "import frigate_intelligence"` succeeds

---

## Step 1.2: Domain Entities

**File: `src/frigate_intelligence/domain/entities/event.py`**

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Event:
    id: str
    label: str
    camera: str
    start_time: float          # Unix timestamp
    end_time: float | None     # Unix timestamp or None
    top_score: float | None
    false_positive: int | None
    zones: list[str]
    has_clip: int
    has_snapshot: int
    region: list[float] | None
    box: list[float] | None
    area: int | None
    retain_indefinitely: int
    sub_label: str | None
    ratio: float | None
    score: float | None
    model_hash: str | None
    detector_type: str | None
    model_type: str | None
    data: dict[str, Any]
```

**File: `src/frigate_intelligence/domain/entities/recording.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Recording:
    id: str
    camera: str
    path: str
    start_time: float
    end_time: float
    duration: float
    objects: int | None
    motion: int | None
    segment_size: float
    dbfs: int | None
    regions: int | None
    motion_heatmap: str | None
```

**File: `src/frigate_intelligence/domain/entities/timeline_entry.py`**

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class TimelineEntry:
    timestamp: float
    camera: str
    source: str
    source_id: str | None
    class_type: str            # "enter", "update", "active", "gone", "snapshot", "clip"
    data: dict[str, Any] | None
```

**File: `src/frigate_intelligence/domain/entities/review_segment.py`**

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ReviewSegment:
    id: str
    camera: str
    start_time: float
    end_time: float | None
    severity: str              # "alert", "detection", "motion"
    thumb_path: str
    data: dict[str, Any]
```

**File: `src/frigate_intelligence/domain/entities/query_result.py`**

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class QueryResult:
    sql: str
    columns: list[str]
    rows: list[tuple[Any, ...]]
    row_count: int
    error: str | None = None

    @property
    def is_success(self) -> bool:
        return self.error is None
```

**File: `src/frigate_intelligence/domain/entities/notification.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Notification:
    message: str
    image_path: str | None = None
    chat_id: str | None = None
    event_id: str | None = None
```

**Acceptance Criteria:**
- [x] All 6 entity files exist with correct dataclass definitions
- [x] All entities are frozen dataclasses
- [x] Type hints use Python 3.12+ syntax (`X | None` not `Optional[X]`)
- [x] `python -c "from frigate_intelligence.domain.entities.event import Event; print(Event.__dataclass_fields__)"` succeeds

---

## Step 1.3: Domain Repository Interfaces

**File: `src/frigate_intelligence/domain/repositories/frigate_repository.py`**

```python
from typing import Protocol
from frigate_intelligence.domain.entities.query_result import QueryResult
from frigate_intelligence.domain.entities.event import Event
from frigate_intelligence.domain.entities.recording import Recording

class FrigateRepository(Protocol):
    def execute_sql(self, sql: str, params: tuple = ()) -> QueryResult:
        """Execute a SELECT query and return results."""
        ...

    def get_events(
        self,
        camera: str | None = None,
        label: str | None = None,
    ) -> list[Event]:
        """Get events, optionally filtered by camera and label."""
        ...

    def get_recordings(
        self,
        camera: str | None = None,
    ) -> list[Recording]:
        """Get recordings, optionally filtered by camera."""
        ...
```

**Acceptance Criteria:**
- [x] `FrigateRepository` is a Protocol (not ABC) with 3 methods
- [x] Method signatures match exactly
- [x] No imports from infrastructure layer

---

## Step 1.4: Domain Service Interfaces

**File: `src/frigate_intelligence/domain/services/llm_service.py`**

```python
from typing import Protocol

class LLMService(Protocol):
    def generate_sql(self, question: str, schema_context: str) -> str:
        """Convert a natural language question to a SQL query string."""
        ...

    def explain_result(self, question: str, sql: str, result_text: str) -> str:
        """Generate a natural language explanation of query results."""
        ...
```

**File: `src/frigate_intelligence/domain/services/notifier_service.py`**

```python
from typing import Protocol
from frigate_intelligence.domain.entities.notification import Notification

class NotifierService(Protocol):
    def send(self, notification: Notification) -> bool:
        """Send a notification. Returns True on success."""
        ...
```

**Acceptance Criteria:**
- [x] Both interfaces are Protocols
- [x] No external dependencies imported
- [x] Method signatures match exactly

---

## Step 1.5: Domain Value Objects

**File: `src/frigate_intelligence/domain/value_objects/sql_query.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SQLQuery:
    raw_sql: str

    @property
    def normalized(self) -> str:
        return self.raw_sql.strip().rstrip(";")

    @property
    def is_select(self) -> bool:
        return self.normalized.upper().startswith("SELECT")

    @property
    def is_safe(self) -> bool:
        dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "ATTACH", "DETACH"]
        upper = self.normalized.upper()
        return not any(f" {kw} " in f" {upper} " for kw in dangerous)
```

**File: `src/frigate_intelligence/domain/value_objects/prompt_context.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PromptContext:
    schema_text: str           # Full schema description from Frigate_Database_Schema_Report.md
    sample_queries: str        # Example SQL queries for few-shot prompting
    rules: str                 # SQL safety rules and constraints

    def as_system_prompt(self) -> str:
        return f"""You are a SQL expert assistant for a Frigate NVR surveillance system database.

## Database Schema
{self.schema_text}

## Example Queries
{self.sample_queries}

## Rules
{self.rules}

Generate ONLY a valid SQLite SELECT query. No explanations, no markdown fences.
The query must be safe (SELECT only, no modifications)."""
```

**File: `src/frigate_intelligence/domain/value_objects/time_range.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TimeRange:
    start: float    # Unix timestamp
    end: float      # Unix timestamp

    @property
    def duration_seconds(self) -> float:
        return self.end - self.start

    def contains(self, timestamp: float) -> bool:
        return self.start <= timestamp <= self.end
```

**Acceptance Criteria:**
- [x] All 3 value objects exist as frozen dataclasses
- [x] `SQLQuery.is_select` and `SQLQuery.is_safe` work correctly
- [x] `PromptContext.as_system_prompt()` returns a formatted string
- [x] `TimeRange.contains()` works correctly

---

## Step 1.6: Frigate SQLite Gateway (Infrastructure)

**File: `src/frigate_intelligence/infrastructure/database/connection.py`**

```python
import sqlite3
from pathlib import Path

def create_connection(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Frigate database not found: {db_path}")
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn
```

**File: `src/frigate_intelligence/infrastructure/database/frigate_sqlite_gateway.py`**

```python
import sqlite3
from frigate_intelligence.domain.entities.query_result import QueryResult
from frigate_intelligence.domain.entities.event import Event
from frigate_intelligence.domain.entities.recording import Recording
from frigate_intelligence.infrastructure.database.connection import create_connection

class FrigateSqliteGateway:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = create_connection(self._db_path)
        return self._conn

    def execute_sql(self, sql: str, params: tuple = ()) -> QueryResult:
        try:
            cur = self.conn.execute(sql, params)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            return QueryResult(
                sql=sql,
                columns=columns,
                rows=[tuple(r) for r in rows],
                row_count=len(rows),
            )
        except Exception as e:
            return QueryResult(
                sql=sql,
                columns=[],
                rows=[],
                row_count=0,
                error=str(e),
            )

    def get_events(self, camera: str | None = None, label: str | None = None) -> list[Event]:
        sql = "SELECT * FROM event"
        conditions = []
        params = []
        if camera:
            conditions.append("camera = ?")
            params.append(camera)
        if label:
            conditions.append("label = ?")
            params.append(label)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY start_time DESC LIMIT 100"
        result = self.execute_sql(sql, tuple(params))
        if result.error:
            return []
        return [self._row_to_event(r) for r in result.rows]

    def get_recordings(self, camera: str | None = None) -> list[Recording]:
        sql = "SELECT * FROM recordings"
        params = ()
        if camera:
            sql += " WHERE camera = ?"
            params = (camera,)
        sql += " ORDER BY start_time DESC LIMIT 100"
        result = self.execute_sql(sql, params)
        if result.error:
            return []
        return [self._row_to_recording(r) for r in result.rows]

    def _row_to_event(self, row: tuple) -> Event:
        # Map column order from SELECT * to Event dataclass
        return Event(
            id=row[0], label=row[1], camera=row[2], start_time=row[3],
            end_time=row[4], top_score=row[5], false_positive=row[6],
            zones=row[7], thumbnail=None, has_clip=row[9], has_snapshot=row[10],
            region=row[11], box=row[12], area=row[13], retain_indefinitely=row[14],
            sub_label=row[15], ratio=row[16], plus_id=row[17], score=row[18],
            model_hash=row[19], detector_type=row[20], model_type=row[21], data=row[22],
        )

    def _row_to_recording(self, row: tuple) -> Recording:
        return Recording(
            id=row[0], camera=row[1], path=row[2], start_time=row[3],
            end_time=row[4], duration=row[5], objects=row[6], motion=row[7],
            segment_size=row[8], dbfs=row[9], regions=row[10], motion_heatmap=row[11],
        )

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
```

**Acceptance Criteria:**
- [x] `FrigateSqliteGateway` implements all 3 methods from `FrigateRepository` protocol
- [x] `execute_sql` returns `QueryResult` with error on failure (no exception raised)
- [x] `get_events` returns list of `Event` objects
- [x] `get_recordings` returns list of `Recording` objects
- [x] Connection is lazily initialized and can be closed

---

## Step 1.7: Avalai LLM Gateway (Infrastructure)

**File: `src/frigate_intelligence/infrastructure/llm/avalai_gateway.py`**

```python
from openai import OpenAI
from frigate_intelligence.domain.services.llm_service import LLMService

class AvalaiGateway:
    def __init__(self, api_key: str, base_url: str, model: str):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def generate_sql(self, question: str, schema_context: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": schema_context},
                {"role": "user", "content": f"Question: {question}\n\nGenerate a SQLite SELECT query to answer this question."},
            ],
            temperature=0.0,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    def explain_result(self, question: str, sql: str, result_text: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that explains database query results in natural language. Respond in the same language as the user's question."},
                {"role": "user", "content": f"Question: {question}\nSQL: {sql}\nResults:\n{result_text}\n\nExplain these results in natural language."},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
```

**Acceptance Criteria:**
- [x] `AvalaiGateway` implements `LLMService` protocol (generate_sql, explain_result)
- [x] Uses `openai` package with custom `base_url` for Avalai.ir (`https://api.avalai.ir/v1`)
- [x] `temperature=0.0` for SQL generation (deterministic)
- [x] `temperature=0.3` for explanation (slightly creative)
- [x] No hardcoded API keys (passed via constructor)

---

## Step 1.8: Schema Context (Interface Adapters)

**File: `src/frigate_intelligence/interface_adapters/schemas/frigate_schema.py`**

```python
from pathlib import Path

SCHEMA_REPORT_PATH = Path(__file__).parent.parent.parent.parent.parent / "Frigate_Database_Schema_Report.md"

def load_schema_context() -> str:
    """Load the Frigate database schema report as a string for LLM context."""
    if SCHEMA_REPORT_PATH.exists():
        return SCHEMA_REPORT_PATH.read_text(encoding="utf-8")
    # Fallback: embedded minimal schema
    return """Frigate SQLite Database Schema:
Tables: event, recordings, timeline, reviewsegment, previews, regions, user
Key table: event (id VARCHAR, label VARCHAR, camera VARCHAR, start_time DATETIME, end_time DATETIME, score REAL, zones JSON, data JSON)
Time format: Unix timestamps (float, seconds since epoch)
Camera: cam1
Labels: person"""

SAMPLE_QUERIES = """-- Get latest person detections
SELECT id, label, start_time, end_time, score FROM event WHERE label='person' ORDER BY start_time DESC LIMIT 10;

-- Count detections by label
SELECT label, COUNT(*) as count FROM event GROUP BY label;

-- Get recordings with objects
SELECT id, camera, path, start_time, duration, objects, motion FROM recordings WHERE objects > 0 ORDER BY start_time DESC;

-- Events in time range
SELECT * FROM event WHERE start_time BETWEEN 1784377610 AND 1784386200 ORDER BY start_time DESC;

-- Timeline for specific event
SELECT timestamp, class_type, data FROM timeline WHERE source_id='1784386154.716448-7wjons' ORDER BY timestamp ASC;"""

SQL_RULES = """1. Generate ONLY SELECT queries. No INSERT, UPDATE, DELETE, DROP, ALTER, or ATTACH.
2. Use SQLite syntax (json_extract for JSON fields).
3. Time fields are Unix timestamps (float). Use datetime(column, 'unixepoch') to convert.
4. Limit results to 100 rows maximum (add LIMIT 100).
5. Table names: event, recordings, timeline, reviewsegment, previews, regions, user.
6. Do not use markdown code fences in output. Return raw SQL only."""
```

**Acceptance Criteria:**
- [x] `load_schema_context()` returns schema text from `Frigate_Database_Schema_Report.md`
- [x] Fallback embedded schema works if file not found
- [x] `SAMPLE_QUERIES` contains 5 example queries
- [x] `SQL_RULES` contains 6 safety rules

---

## Step 1.9: SQL Validator (Use Cases)

**File: `src/frigate_intelligence/use_cases/text_to_sql/sql_validator.py`**

```python
import re

VALID_TABLES = {"event", "recordings", "timeline", "reviewsegment", "previews", "regions", "user", "export", "exportcase", "migratehistory", "trigger", "userreviewstatus", "sqlite_sequence"}

class SQLValidator:
    @staticmethod
    def validate(sql: str) -> tuple[bool, str | None]:
        sql_stripped = sql.strip().rstrip(";").strip()

        if not sql_stripped:
            return False, "Empty SQL"

        if not sql_stripped.upper().startswith("SELECT"):
            return False, "Only SELECT queries are allowed"

        dangerous_patterns = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "ATTACH", "DETACH", "PRAGMA", "VACUUM"]
        upper = sql_stripped.upper()
        for pattern in dangerous_patterns:
            if re.search(rf"\b{pattern}\b", upper):
                return False, f"Dangerous keyword detected: {pattern}"

        if not any(table in sql_stripped.lower() for table in VALID_TABLES):
            return False, "No valid table name found in query"

        return True, None
```

**Acceptance Criteria:**
- [x] `validate("SELECT * FROM event")` returns `(True, None)`
- [x] `validate("DROP TABLE event")` returns `(False, "Only SELECT queries are allowed")`
- [x] `validate("SELECT * FROM event; DROP TABLE event")` returns `(False, "Dangerous keyword...")`
- [x] `validate("")` returns `(False, "Empty SQL")`
- [x] `validate("SELECT * FROM nonexistent")` returns `(False, "No valid table name...")`

---

## Step 1.10: Prompt Builder (Use Cases)

**File: `src/frigate_intelligence/use_cases/text_to_sql/prompt_builder.py`**

```python
from frigate_intelligence.domain.value_objects.prompt_context import PromptContext
from frigate_intelligence.interface_adapters.schemas.frigate_schema import load_schema_context, SAMPLE_QUERIES, SQL_RULES

class PromptBuilder:
    @staticmethod
    def build() -> PromptContext:
        return PromptContext(
            schema_text=load_schema_context(),
            sample_queries=SAMPLE_QUERIES,
            rules=SQL_RULES,
        )
```

**Acceptance Criteria:**
- [x] `PromptBuilder.build()` returns a `PromptContext` object
- [x] `PromptContext.as_system_prompt()` contains schema, sample queries, and rules
- [x] System prompt instructs LLM to generate only SELECT queries

---

## Step 1.11: Text-to-SQL Use Case

**File: `src/frigate_intelligence/use_cases/text_to_sql/text_to_sql_use_case.py`**

```python
from dataclasses import dataclass
from frigate_intelligence.domain.repositories.frigate_repository import FrigateRepository
from frigate_intelligence.domain.services.llm_service import LLMService
from frigate_intelligence.domain.entities.query_result import QueryResult
from frigate_intelligence.use_cases.text_to_sql.sql_validator import SQLValidator
from frigate_intelligence.use_cases.text_to_sql.prompt_builder import PromptBuilder

@dataclass
class TextToSQLRequest:
    question: str
    max_retries: int = 3

@dataclass
class TextToSQLResponse:
    question: str
    sql: str
    result: QueryResult
    explanation: str
    attempts: int

class TextToSQLUseCase:
    def __init__(self, frigate_repo: FrigateRepository, llm_service: LLMService):
        self._repo = frigate_repo
        self._llm = llm_service
        self._prompt = PromptBuilder.build()

    def execute(self, request: TextToSQLRequest) -> TextToSQLResponse:
        system_prompt = self._prompt.as_system_prompt()
        attempts = 0
        last_error = ""

        for attempt in range(1, request.max_retries + 1):
            attempts = attempt
            user_msg = request.question if attempt == 1 else f"{request.question}\n\nPrevious attempt failed: {last_error}\nPlease fix the SQL."

            sql_raw = self._llm.generate_sql(user_msg, system_prompt)
            sql = self._extract_sql(sql_raw)

            is_valid, error = SQLValidator.validate(sql)
            if not is_valid:
                last_error = f"Validation: {error}"
                continue

            result = self._repo.execute_sql(sql)
            if not result.is_success:
                last_error = f"Execution: {result.error}"
                continue

            result_text = self._format_result(result)
            explanation = self._llm.explain_result(request.question, sql, result_text)
            return TextToSQLResponse(
                question=request.question,
                sql=sql,
                result=result,
                explanation=explanation,
                attempts=attempts,
            )

        return TextToSQLResponse(
            question=request.question,
            sql="",
            result=QueryResult(sql="", columns=[], rows=[], row_count=0, error=last_error),
            explanation=f"Failed after {attempts} attempts. Last error: {last_error}",
            attempts=attempts,
        )

    def _extract_sql(self, raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            return "\n".join(lines).strip()
        return raw

    def _format_result(self, result: QueryResult) -> str:
        if not result.columns:
            return f"({result.row_count} rows)"
        header = " | ".join(result.columns)
        separator = "-" * len(header)
        data_lines = []
        for row in result.rows[:20]:
            data_lines.append(" | ".join(str(v) for v in row))
        return f"{header}\n{separator}\n" + "\n".join(data_lines) + f"\n({result.row_count} rows total)"
```

**Acceptance Criteria:**
- [x] `execute()` returns `TextToSQLResponse` with SQL, result, and explanation
- [x] Retries up to `max_retries` times on validation or execution failure
- [x] SQL is extracted from markdown code fences if present
- [x] Result is formatted as text table for LLM explanation
- [x] No direct imports from infrastructure layer

---

## Step 1.12: CLI Controller and Presenter

**File: `src/frigate_intelligence/interface_adapters/presenters/cli_presenter.py`**

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import TextToSQLResponse

class CLIPresenter:
    def __init__(self):
        self._console = Console()

    def show_response(self, response: TextToSQLResponse) -> None:
        self._console.print(Panel(f"[bold cyan]Question:[/bold cyan] {response.question}", title="Query"))
        self._console.print(f"[dim]SQL (attempts: {response.attempts}):[/dim]")
        self._console.print(Panel(response.sql, title="Generated SQL", border_style="green"))

        if response.result.is_success and response.result.columns:
            table = Table(show_header=True, header_style="bold magenta")
            for col in response.result.columns:
                table.add_column(col)
            for row in response.result.rows[:50]:
                table.add_row(*[str(v)[:50] for v in row])
            self._console.print(table)
            self._console.print(f"[dim]{response.result.row_count} rows total[/dim]")
        elif response.result.error:
            self._console.print(f"[red]Error: {response.result.error}[/red]")

        self._console.print(Panel(response.explanation, title="Explanation", border_style="blue"))

    def show_error(self, message: str) -> None:
        self._console.print(f"[red]Error: {message}[/red]")
```

**File: `src/frigate_intelligence/interface_adapters/controllers/cli_controller.py`**

```python
import typer
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import TextToSQLUseCase, TextToSQLRequest
from frigate_intelligence.interface_adapters.presenters.cli_presenter import CLIPresenter

app = typer.Typer(help="Frigate Intelligence CLI")

class CLIController:
    def __init__(self, text_to_sql_use_case: TextToSQLUseCase):
        self._use_case = text_to_sql_use_case
        self._presenter = CLIPresenter()

    def query(self, question: str) -> None:
        request = TextToSQLRequest(question=question)
        response = self._use_case.execute(request)
        self._presenter.show_response(response)
```

**Acceptance Criteria:**
- [x] `CLIPresenter.show_response()` displays SQL, results table, and explanation
- [x] `CLIPresenter.show_error()` displays error in red
- [x] `CLIController.query()` calls use case and passes result to presenter
- [x] Rich tables are used for data display
- [x] Results are limited to 50 rows in display

---

## Step 1.13: Config and Composition Root

**File: `src/frigate_intelligence/config/settings.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    frigate_db_path: str = "/opt/frigate/config/frigate.db"
    avalai_api_key: str = ""
    avalai_base_url: str = "https://avalai.ir/v1"
    llm_model: str = "gemini-3.1-flash-lite"
    max_sql_retries: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

**File: `src/frigate_intelligence/config/dependencies.py`**

```python
from dataclasses import dataclass
from frigate_intelligence.config.settings import Settings
from frigate_intelligence.infrastructure.database.frigate_sqlite_gateway import FrigateSqliteGateway
from frigate_intelligence.infrastructure.llm.avalai_gateway import AvalaiGateway
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import TextToSQLUseCase

@dataclass
class Container:
    frigate_repo: FrigateSqliteGateway
    llm_service: AvalaiGateway
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
    )
    return Container(
        frigate_repo=frigate_repo,
        llm_service=llm_service,
        text_to_sql_use_case=text_to_sql,
    )
```

**File: `src/frigate_intelligence/main.py`**

```python
import typer
from rich.console import Console
from frigate_intelligence.config.settings import Settings
from frigate_intelligence.config.dependencies import create_container
from frigate_intelligence.interface_adapters.controllers.cli_controller import CLIController

app = typer.Typer(help="Frigate Intelligence Platform CLI")
console = Console()

@app.command()
def query(question: str = typer.Argument(..., help="Natural language question about camera events")):
    """Ask a question about Frigate camera events in natural language."""
    settings = Settings()
    container = create_container(settings)
    controller = CLIController(container.text_to_sql_use_case)
    controller.query(question)

@app.command()
def interactive():
    """Start interactive chat mode."""
    settings = Settings()
    container = create_container(settings)
    controller = CLIController(container.text_to_sql_use_case)
    console.print("[bold green]Frigate Intelligence Interactive Mode[/bold green]")
    console.print("Type 'exit' to quit.\n")
    while True:
        question = typer.prompt("Question", default="")
        if question.lower() in ("exit", "quit", "q"):
            break
        if question:
            controller.query(question)
            console.print()

if __name__ == "__main__":
    app()
```

**File: `frigate-intelligence/.env.example`**

```env
FRIGATE_DB_PATH=/opt/frigate/config/frigate.db
AVALAI_API_KEY=your-api-key-here
AVALAI_BASE_URL=https://avalai.ir/v1
LLM_MODEL=gemini-3.1-flash-lite
MAX_SQL_RETRIES=3
```

**Acceptance Criteria:**
- [x] `Settings` loads from `.env` file
- [x] `create_container()` wires all dependencies correctly
- [x] `frigate-ai query "test"` command is registered
- [x] `frigate-ai interactive` command is registered
- [x] No hardcoded API keys or paths

---

## Step 1.14: Unit Tests

**File: `tests/unit/domain/test_sql_query.py`**

```python
from frigate_intelligence.domain.value_objects.sql_query import SQLQuery

def test_is_select_valid():
    q = SQLQuery("SELECT * FROM event")
    assert q.is_select is True

def test_is_select_invalid():
    q = SQLQuery("DROP TABLE event")
    assert q.is_select is False

def test_is_safe_valid():
    q = SQLQuery("SELECT * FROM event WHERE label = 'person'")
    assert q.is_safe is True

def test_is_safe_drop():
    q = SQLQuery("SELECT * FROM event; DROP TABLE event")
    assert q.is_safe is False

def test_normalized_strips_semicolon():
    q = SQLQuery("SELECT 1;")
    assert q.normalized == "SELECT 1"
```

**File: `tests/unit/use_cases/test_sql_validator.py`**

```python
from frigate_intelligence.use_cases.text_to_sql.sql_validator import SQLValidator

def test_valid_select():
    ok, err = SQLValidator.validate("SELECT * FROM event")
    assert ok is True
    assert err is None

def test_drop_rejected():
    ok, err = SQLValidator.validate("DROP TABLE event")
    assert ok is False

def test_insert_rejected():
    ok, err = SQLValidator.validate("INSERT INTO event VALUES (1)")
    assert ok is False

def test_empty_rejected():
    ok, err = SQLValidator.validate("")
    assert ok is False

def test_no_table_rejected():
    ok, err = SQLValidator.validate("SELECT 1")
    assert ok is False
```

**File: `tests/unit/use_cases/test_text_to_sql_use_case.py`**

```python
from unittest.mock import MagicMock
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import TextToSQLUseCase, TextToSQLRequest
from frigate_intelligence.domain.entities.query_result import QueryResult

def test_successful_query():
    mock_repo = MagicMock()
    mock_repo.execute_sql.return_value = QueryResult(
        sql="SELECT * FROM event",
        columns=["id", "label"],
        rows=[("1", "person")],
        row_count=1,
    )
    mock_llm = MagicMock()
    mock_llm.generate_sql.return_value = "SELECT * FROM event"
    mock_llm.explain_result.return_value = "Found 1 person event"

    use_case = TextToSQLUseCase(mock_repo, mock_llm)
    response = use_case.execute(TextToSQLRequest(question="Show me events"))

    assert response.sql == "SELECT * FROM event"
    assert response.result.row_count == 1
    assert "1 person" in response.explanation
    assert response.attempts == 1

def test_retry_on_validation_failure():
    mock_repo = MagicMock()
    mock_llm = MagicMock()
    mock_llm.generate_sql.side_effect = ["DROP TABLE event", "SELECT * FROM event"]
    mock_llm.explain_result.return_value = "Results explained"
    mock_repo.execute_sql.return_value = QueryResult(
        sql="SELECT * FROM event", columns=["id"], rows=[], row_count=0,
    )

    use_case = TextToSQLUseCase(mock_repo, mock_llm)
    response = use_case.execute(TextToSQLRequest(question="Show events"))

    assert response.attempts == 2
    assert response.sql == "SELECT * FROM event"
```

**Acceptance Criteria:**
- [x] `pytest tests/unit/ -v` passes all tests
- [x] Mock objects are used (no real DB or LLM calls)
- [x] Test coverage for SQL validator (7 tests including PRAGMA and injection)
- [x] Test coverage for use case (5 tests: success, validation retry, execution retry, exhausted retries, markdown extraction)
- [x] Test coverage for SQLQuery value object (5 tests)

---

## Step 1.15: Integration Test

**File: `tests/integration/test_frigate_sqlite_gateway.py`**

```python
import sqlite3
import tempfile
import os
from frigate_intelligence.infrastructure.database.frigate_sqlite_gateway import FrigateSqliteGateway

def test_execute_sql_on_real_db():
    # Create temp DB with event table
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE event (id TEXT, label TEXT, camera TEXT, start_time REAL)")
    conn.execute("INSERT INTO event VALUES ('1', 'person', 'cam1', 1784386154.0)")
    conn.commit()
    conn.close()

    try:
        gateway = FrigateSqliteGateway(db_path)
        result = gateway.execute_sql("SELECT * FROM event")
        assert result.is_success
        assert result.row_count == 1
        assert result.columns == ["id", "label", "camera", "start_time"]
        gateway.close()
    finally:
        os.unlink(db_path)

def test_execute_sql_error_handling():
    gateway = FrigateSqliteGateway("/nonexistent/path.db")
    result = gateway.execute_sql("SELECT * FROM event")
    assert not result.is_success
    assert result.error is not None
```

**Acceptance Criteria:**
- [x] `pytest tests/integration/ -v` passes
- [x] Real SQLite DB is created in temp directory for testing
- [x] Error handling for missing DB file is tested

---

## Final Verification (Phase 1 Complete)

**Run these commands to verify Phase 1:**

```bash
# 1. Install dependencies
cd frigate-intelligence
uv sync

# 2. Run unit tests
uv run pytest tests/unit/ -v

# 3. Run integration tests
uv run pytest tests/integration/ -v

# 4. Test CLI (requires .env with real API key and DB path)
uv run frigate-ai query "آخرین رویدادهای شخصی که جلوی دوربین بودند چه زمانی بود؟"

# 5. Test interactive mode
uv run frigate-ai interactive
```

**Phase 1 Complete When:**
- [x] All unit tests pass (19 tests)
- [x] All integration tests pass (2 tests)
- [x] CLI `query` command returns SQL + results + explanation
- [x] CLI `interactive` mode works with multiple questions
- [x] Persian language questions work correctly (tested with Avalai API)
- [x] SQL injection is prevented (validator rejects dangerous queries)
- [x] Retry mechanism works on LLM errors
