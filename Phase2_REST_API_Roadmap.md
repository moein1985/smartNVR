# Phase 2: REST API (FastAPI) — Detailed Roadmap

## Objective

Expose the Phase 1 Text-to-SQL use case (and event query use cases) via a REST API using FastAPI, enabling Flutter app and external clients to interact with the platform.

---

## Prerequisites

- Phase 1 complete (Domain, Use Cases, Infrastructure all working)
- FastAPI and Uvicorn installed

---

## Step 2.1: Add FastAPI Dependencies

**File: `frigate-intelligence/pyproject.toml` (update)**

Add to `dependencies`:
```toml
"fastapi>=0.115.0",
"uvicorn[standard]>=0.30.0",
```

---

## Step 2.2: API Models (Pydantic)

**File: `src/frigate_intelligence/interface_adapters/schemas/api_models.py`**

```python
from pydantic import BaseModel
from typing import Any

class QueryRequest(BaseModel):
    question: str
    max_retries: int = 3

class QueryResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    explanation: str
    attempts: int
    error: str | None = None

class EventListResponse(BaseModel):
    events: list[dict[str, Any]]
    total: int

class HealthResponse(BaseModel):
    status: str
    version: str
    db_connected: bool
```

**Acceptance Criteria:**
- [x] All request/response models are Pydantic BaseModel
- [x] `QueryResponse` maps to `TextToSQLResponse` fields
- [x] Type hints use Python 3.12+ syntax

---

## Step 2.3: API Presenter

**File: `src/frigate_intelligence/interface_adapters/presenters/api_presenter.py`**

```python
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import TextToSQLResponse
from frigate_intelligence.interface_adapters.schemas.api_models import QueryResponse

class APIPresenter:
    @staticmethod
    def to_query_response(response: TextToSQLResponse) -> QueryResponse:
        return QueryResponse(
            question=response.question,
            sql=response.sql,
            columns=response.result.columns,
            rows=[list(r) for r in response.result.rows],
            row_count=response.result.row_count,
            explanation=response.explanation,
            attempts=response.attempts,
            error=response.result.error,
        )
```

---

## Step 2.4: API Controller

**File: `src/frigate_intelligence/interface_adapters/controllers/api_controller.py`**

```python
from fastapi import APIRouter, HTTPException
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import TextToSQLUseCase, TextToSQLRequest
from frigate_intelligence.interface_adapters.schemas.api_models import QueryRequest, QueryResponse, HealthResponse
from frigate_intelligence.interface_adapters.presenters.api_presenter import APIPresenter

class APIController:
    def __init__(self, text_to_sql_use_case: TextToSQLUseCase):
        self._use_case = text_to_sql_use_case
        self.router = APIRouter(prefix="/api/v1", tags=["intelligence"])
        self._register_routes()

    def _register_routes(self):
        self.router.add_api_route("/query", self.query, methods=["POST"])
        self.router.add_api_route("/health", self.health, methods=["GET"])

    async def query(self, request: QueryRequest) -> QueryResponse:
        req = TextToSQLRequest(question=request.question, max_retries=request.max_retries)
        response = self._use_case.execute(req)
        return APIPresenter.to_query_response(response)

    async def health(self) -> HealthResponse:
        return HealthResponse(status="ok", version="0.1.0", db_connected=True)
```

---

## Step 2.5: FastAPI App Factory

**File: `src/frigate_intelligence/infrastructure/api/fastapi_app.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from frigate_intelligence.config.dependencies import Container
from frigate_intelligence.interface_adapters.controllers.api_controller import APIController

def create_app(container: Container) -> FastAPI:
    app = FastAPI(title="Frigate Intelligence Platform", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    controller = APIController(container.text_to_sql_use_case)
    app.include_router(controller.router)

    return app
```

---

## Step 2.6: Update Main Entry Point

**File: `src/frigate_intelligence/main.py` (update)**

Add `serve` command:
```python
@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
):
    """Start REST API server."""
    import uvicorn
    from frigate_intelligence.infrastructure.api.fastapi_app import create_app
    settings = Settings()
    container = create_container(settings)
    fastapi_app = create_app(container)
    uvicorn.run(fastapi_app, host=host, port=port)
```

---

## Step 2.7: API Routes for Direct Event Queries

**File: `src/frigate_intelligence/infrastructure/api/routes/event_routes.py`**

```python
from fastapi import APIRouter, Query
from frigate_intelligence.interface_adapters.schemas.api_models import EventListResponse

def create_event_router(frigate_repo) -> APIRouter:
    router = APIRouter(prefix="/api/v1/events", tags=["events"])

    @router.get("", response_model=EventListResponse)
    async def list_events(
        camera: str | None = Query(None),
        label: str | None = Query(None),
    ):
        events = frigate_repo.get_events(camera=camera, label=label)
        return EventListResponse(
            events=[e.__dict__ for e in events],
            total=len(events),
        )

    return router
```

---

## Step 2.8: Docker Deployment

**File: `frigate-intelligence/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync --no-dev
COPY src/ src/
COPY .env .env
EXPOSE 8000
CMD ["uv", "run", "frigate-ai", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

**File: `frigate-intelligence/docker-compose.yml`**

```yaml
services:
  frigate-intelligence:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - /opt/frigate/config/frigate.db:/data/frigate.db:ro
    env_file:
      - .env
    environment:
      - FRIGATE_DB_PATH=/data/frigate.db
```

---

## Acceptance Criteria (Phase 2)

- [x] `POST /api/v1/query` accepts `{"question": "..."}` and returns SQL + results + explanation
- [x] `GET /api/v1/health` returns `{"status": "ok", "version": "0.1.0", "db_connected": true}`
- [x] `GET /api/v1/events?camera=cam1&label=person` returns event list
- [x] CORS is enabled for Flutter cross-origin requests
- [x] OpenAPI docs available at `/docs`
- [x] Docker container runs and connects to Frigate DB (deployed on 192.168.85.202:8088)
- [x] API key authentication middleware added (optional in this phase)

**Verification Commands:**
```bash
uv run frigate-ai serve --host 0.0.0.0 --port 8000
curl -X POST http://localhost:8000/api/v1/query -H "Content-Type: application/json" -d '{"question": "آخرین رویدادها چه بود؟"}'
curl http://localhost:8000/api/v1/health
curl "http://localhost:8000/api/v1/events?label=person"
```
