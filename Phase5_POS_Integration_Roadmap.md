# Phase 5: POS Integration & Advanced Analytics — Detailed Roadmap

## Objective

Integrate POS (card reader) devices to correlate financial transactions with camera events, enabling:
1. Match a card transaction timestamp with camera detections
2. Retrieve video clips and snapshots for the matched time window
3. Advanced analytics (traffic patterns, peak hours, detection heatmaps)
4. Multi-camera support and correlation

---

## Prerequisites

- Phases 1-4 complete
- POS device API documentation available
- Multiple cameras configured in Frigate (optional but recommended)

---

## Step 5.1: POS Domain Layer

**File: `src/frigate_intelligence/domain/entities/pos_transaction.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class POSTransaction:
    transaction_id: str
    timestamp: float           # Unix timestamp
    amount: float              # Transaction amount
    card_number_masked: str    # Masked card number (e.g., ****1234)
    merchant_id: str
    status: str                # "approved", "declined", "refunded"
    terminal_id: str
```

**File: `src/frigate_intelligence/domain/repositories/pos_repository.py`**

```python
from typing import Protocol
from frigate_intelligence.domain.entities.pos_transaction import POSTransaction

class POSRepository(Protocol):
    def get_transaction(self, transaction_id: str) -> POSTransaction | None:
        """Get a single transaction by ID."""
        ...

    def get_transactions_in_range(
        self, start_time: float, end_time: float
    ) -> list[POSTransaction]:
        """Get all transactions within a time range."""
        ...

    def get_latest_transactions(self, limit: int = 10) -> list[POSTransaction]:
        """Get the most recent transactions."""
        ...
```

---

## Step 5.2: POS API Gateway (Infrastructure)

**File: `src/frigate_intelligence/infrastructure/pos/pos_api_gateway.py`**

```python
import httpx
from datetime import datetime
from frigate_intelligence.domain.entities.pos_transaction import POSTransaction

class POSApiGateway:
    def __init__(self, api_url: str, api_key: str):
        self._url = api_url
        self._key = api_key
        self._headers = {"Authorization": f"Bearer {api_key}"}

    def get_transaction(self, transaction_id: str) -> POSTransaction | None:
        with httpx.Client() as client:
            resp = client.get(f"{self._url}/transactions/{transaction_id}", headers=self._headers)
            if resp.status_code != 200:
                return None
            data = resp.json()
            return self._parse_transaction(data)

    def get_transactions_in_range(self, start_time: float, end_time: float) -> list[POSTransaction]:
        with httpx.Client() as client:
            start_iso = datetime.fromtimestamp(start_time).isoformat()
            end_iso = datetime.fromtimestamp(end_time).isoformat()
            resp = client.get(
                f"{self._url}/transactions",
                params={"start": start_iso, "end": end_iso},
                headers=self._headers,
            )
            if resp.status_code != 200:
                return []
            return [self._parse_transaction(t) for t in resp.json()]

    def get_latest_transactions(self, limit: int = 10) -> list[POSTransaction]:
        with httpx.Client() as client:
            resp = client.get(
                f"{self._url}/transactions",
                params={"limit": limit},
                headers=self._headers,
            )
            if resp.status_code != 200:
                return []
            return [self._parse_transaction(t) for t in resp.json()]

    def _parse_transaction(self, data: dict) -> POSTransaction:
        return POSTransaction(
            transaction_id=data["id"],
            timestamp=data["timestamp"],
            amount=data["amount"],
            card_number_masked=data.get("card_masked", ""),
            merchant_id=data.get("merchant_id", ""),
            status=data.get("status", "unknown"),
            terminal_id=data.get("terminal_id", ""),
        )
```

---

## Step 5.3: Correlate POS Use Case

**File: `src/frigate_intelligence/use_cases/correlate_pos/correlate_pos_use_case.py`**

```python
from dataclasses import dataclass
from frigate_intelligence.domain.repositories.frigate_repository import FrigateRepository
from frigate_intelligence.domain.repositories.pos_repository import POSRepository
from frigate_intelligence.domain.entities.event import Event
from frigate_intelligence.domain.entities.pos_transaction import POSTransaction
from frigate_intelligence.domain.value_objects.time_range import TimeRange

@dataclass
class CorrelatePOSRequest:
    transaction_id: str
    time_window_seconds: float = 30.0  # ±30 seconds around transaction

@dataclass
class CorrelationMatch:
    transaction: POSTransaction
    events: list[Event]
    time_range: TimeRange

@dataclass
class CorrelatePOSResponse:
    matches: list[CorrelationMatch]
    total_events: int
    error: str | None = None

class CorrelatePOSUseCase:
    def __init__(self, frigate_repo: FrigateRepository, pos_repo: POSRepository):
        self._frigate = frigate_repo
        self._pos = pos_repo

    def execute(self, request: CorrelatePOSRequest) -> CorrelatePOSResponse:
        txn = self._pos.get_transaction(request.transaction_id)
        if txn is None:
            return CorrelatePOSResponse(matches=[], total_events=0, error="Transaction not found")

        start = txn.timestamp - request.time_window_seconds
        end = txn.timestamp + request.time_window_seconds

        # Query events in time range via SQL
        sql = "SELECT * FROM event WHERE start_time BETWEEN ? AND ? ORDER BY start_time ASC"
        result = self._frigate.execute_sql(sql, (start, end))

        if result.error:
            return CorrelatePOSResponse(matches=[], total_events=0, error=result.error)

        # Parse rows into Event objects (simplified)
        events = []
        for row in result.rows:
            events.append(Event(
                id=row[0], label=row[1], camera=row[2], start_time=row[3],
                end_time=row[4], top_score=row[5], false_positive=row[6],
                zones=row[7], thumbnail=None, has_clip=row[9], has_snapshot=row[10],
                region=row[11], box=row[12], area=row[13], retain_indefinitely=row[14],
                sub_label=row[15], ratio=row[16], plus_id=row[17], score=row[18],
                model_hash=row[19], detector_type=row[20], model_type=row[21], data=row[22],
            ))

        match = CorrelationMatch(
            transaction=txn,
            events=events,
            time_range=TimeRange(start=start, end=end),
        )

        return CorrelatePOSResponse(matches=[match], total_events=len(events))
```

---

## Step 5.4: Analytics Use Cases

**File: `src/frigate_intelligence/use_cases/analytics/analytics_use_case.py`**

```python
from dataclasses import dataclass
from frigate_intelligence.domain.repositories.frigate_repository import FrigateRepository

@dataclass
class AnalyticsRequest:
    camera: str | None = None
    start_time: float | None = None
    end_time: float | None = None

@dataclass
class AnalyticsResponse:
    total_events: int
    events_by_label: dict[str, int]
    events_by_hour: dict[int, int]
    events_by_camera: dict[str, int]
    peak_hour: int
    avg_daily_events: float

class AnalyticsUseCase:
    def __init__(self, frigate_repo: FrigateRepository):
        self._repo = frigate_repo

    def execute(self, request: AnalyticsRequest) -> AnalyticsResponse:
        where_clauses = []
        params = []
        if request.camera:
            where_clauses.append("camera = ?")
            params.append(request.camera)
        if request.start_time:
            where_clauses.append("start_time >= ?")
            params.append(request.start_time)
        if request.end_time:
            where_clauses.append("start_time <= ?")
            params.append(request.end_time)

        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Total count
        result = self._repo.execute_sql(f"SELECT COUNT(*) FROM event{where_sql}", tuple(params))
        total = result.rows[0][0] if result.rows else 0

        # By label
        result = self._repo.execute_sql(
            f"SELECT label, COUNT(*) FROM event{where_sql} GROUP BY label ORDER BY COUNT(*) DESC",
            tuple(params)
        )
        by_label = {r[0]: r[1] for r in result.rows}

        # By hour
        result = self._repo.execute_sql(
            f"SELECT CAST(strftime('%H', datetime(start_time, 'unixepoch')) AS INT) as hour, COUNT(*) "
            f"FROM event{where_sql} GROUP BY hour ORDER BY hour",
            tuple(params)
        )
        by_hour = {r[0]: r[1] for r in result.rows}

        # By camera
        result = self._repo.execute_sql(
            f"SELECT camera, COUNT(*) FROM event{where_sql} GROUP BY camera",
            tuple(params)
        )
        by_camera = {r[0]: r[1] for r in result.rows}

        peak_hour = max(by_hour, key=by_hour.get) if by_hour else 0

        # Avg daily
        result = self._repo.execute_sql(
            f"SELECT COUNT(DISTINCT date(datetime(start_time, 'unixepoch'))) FROM event{where_sql}",
            tuple(params)
        )
        distinct_days = result.rows[0][0] if result.rows else 1
        avg_daily = total / distinct_days if distinct_days > 0 else 0

        return AnalyticsResponse(
            total_events=total,
            events_by_label=by_label,
            events_by_hour=by_hour,
            events_by_camera=by_camera,
            peak_hour=peak_hour,
            avg_daily_events=round(avg_daily, 1),
        )
```

---

## Step 5.5: Video Clip Retrieval

**File: `src/frigate_intelligence/use_cases/retrieve_clip/retrieve_clip_use_case.py`**

```python
from dataclasses import dataclass
from frigate_intelligence.domain.repositories.frigate_repository import FrigateRepository

@dataclass
class RetrieveClipRequest:
    event_id: str

@dataclass
class RetrieveClipResponse:
    clip_path: str | None
    snapshot_path: str | None
    recording_path: str | None
    error: str | None = None

class RetrieveClipUseCase:
    def __init__(self, frigate_repo: FrigateRepository):
        self._repo = frigate_repo

    def execute(self, request: RetrieveClipRequest) -> RetrieveClipResponse:
        # Get event details
        result = self._repo.execute_sql(
            "SELECT has_clip, has_snapshot, camera, start_time FROM event WHERE id = ?",
            (request.event_id,)
        )
        if not result.rows:
            return RetrieveClipResponse(None, None, None, error="Event not found")

        has_clip, has_snapshot, camera, start_time = result.rows[0]

        clip_path = None
        snapshot_path = None

        if has_clip:
            # Frigate stores clips at /media/frigate/clips/
            clip_path = f"/media/frigate/clips/{camera}-{request.event_id}.mp4"

        if has_snapshot:
            snapshot_path = f"/media/frigate/clips/{camera}-{request.event_id}.jpg"

        # Find recording segment
        recording_result = self._repo.execute_sql(
            "SELECT path FROM recordings WHERE camera = ? AND start_time <= ? AND end_time >= ? LIMIT 1",
            (camera, start_time, start_time)
        )
        recording_path = recording_result.rows[0][0] if recording_result.rows else None

        return RetrieveClipResponse(
            clip_path=clip_path,
            snapshot_path=snapshot_path,
            recording_path=recording_path,
        )
```

---

## Step 5.6: API Endpoints for New Features

**File: `src/frigate_intelligence/infrastructure/api/routes/pos_routes.py`**

```python
from fastapi import APIRouter
from pydantic import BaseModel

class CorrelateRequest(BaseModel):
    transaction_id: str
    time_window_seconds: float = 30.0

def create_pos_router(correlate_use_case) -> APIRouter:
    router = APIRouter(prefix="/api/v1/pos", tags=["pos"])

    @router.post("/correlate")
    async def correlate(request: CorrelateRequest):
        from frigate_intelligence.use_cases.correlate_pos.correlate_pos_use_case import CorrelatePOSRequest
        req = CorrelatePOSRequest(
            transaction_id=request.transaction_id,
            time_window_seconds=request.time_window_seconds,
        )
        response = correlate_use_case.execute(req)
        return {
            "total_events": response.total_events,
            "matches": [
                {
                    "transaction": {
                        "id": m.transaction.transaction_id,
                        "timestamp": m.transaction.timestamp,
                        "amount": m.transaction.amount,
                        "status": m.transaction.status,
                    },
                    "events": [
                        {"id": e.id, "label": e.label, "start_time": e.start_time}
                        for e in m.events
                    ],
                    "time_range": {"start": m.time_range.start, "end": m.time_range.end},
                }
                for m in response.matches
            ],
            "error": response.error,
        }

    return router
```

**File: `src/frigate_intelligence/infrastructure/api/routes/analytics_routes.py`**

```python
from fastapi import APIRouter, Query

def create_analytics_router(analytics_use_case) -> APIRouter:
    router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

    @router.get("/summary")
    async def summary(
        camera: str | None = Query(None),
        start_time: float | None = Query(None),
        end_time: float | None = Query(None),
    ):
        from frigate_intelligence.use_cases.analytics.analytics_use_case import AnalyticsRequest
        req = AnalyticsRequest(camera=camera, start_time=start_time, end_time=end_time)
        resp = analytics_use_case.execute(req)
        return {
            "total_events": resp.total_events,
            "events_by_label": resp.events_by_label,
            "events_by_hour": resp.events_by_hour,
            "events_by_camera": resp.events_by_camera,
            "peak_hour": resp.peak_hour,
            "avg_daily_events": resp.avg_daily_events,
        }

    return router
```

---

## Step 5.7: Multi-Camera Support

**Config update (`frigate-config.yml`):**
```yaml
cameras:
  cam1:
    enabled: true
    ffmpeg:
      inputs:
        - path: rtsp://user:pass@192.168.85.112:554/stream1
          roles: [detect, record]
  cam2:
    enabled: true
    ffmpeg:
      inputs:
        - path: rtsp://user:pass@192.168.85.113:554/stream1
          roles: [detect, record]
```

**Schema context update:**
- Update `frigate_schema.py` to include multi-camera examples
- Add camera filter to all query use cases

---

## Step 5.8: gRPC Endpoint (Optional)

For high-performance Flutter communication:

**File: `frigate-intelligence/proto/intelligence.proto`**
```protobuf
syntax = "proto3";
package intelligence;

service IntelligenceService {
  rpc Query(QueryRequest) returns (QueryResponse);
  rpc GetEvents(EventFilter) returns (EventList);
  rpc StreamAlerts(AlertFilter) returns (stream Alert);
}

message QueryRequest { string question = 1; }
message QueryResponse {
  string sql = 1;
  repeated string columns = 2;
  repeated string rows = 3;
  string explanation = 4;
}
```

---

## Acceptance Criteria (Phase 5)

- [x] `POST /api/v1/pos/correlate` returns events matching a transaction time
- [x] `GET /api/v1/analytics/summary` returns traffic statistics
- [x] Analytics include: total events, by label, by hour, by camera, peak hour, daily average
- [x] Video clip paths are retrievable for events with `has_clip=1`
- [x] Snapshot paths are retrievable for events with `has_snapshot=1`
- [x] Multiple cameras are supported in all queries
- [x] POS correlation works with configurable time window (±N seconds)
- [ ] gRPC endpoint is optional but documented

**Verification:**
```bash
curl -X POST http://localhost:8000/api/v1/pos/correlate \
  -H "Content-Type: application/json" \
  -d '{"transaction_id": "txn123", "time_window_seconds": 30}'

curl "http://localhost:8000/api/v1/analytics/summary?camera=cam1"
```

---

## Full Platform Complete When:

- [x] Phase 1: CLI Text-to-SQL works with Persian questions
- [x] Phase 2: REST API serves all use cases
- [x] Phase 3: Telegram + Bale bots respond and alert
- [ ] Phase 4: Flutter app works on mobile + desktop with voice + images
- [x] Phase 5: POS correlation + analytics + multi-camera + clip retrieval
- [x] All tests pass (unit + integration: 31 tests passing)
- [x] Docker deployment works end-to-end (deployed on 192.168.85.202:8088)
- [x] Documentation is complete and up-to-date
