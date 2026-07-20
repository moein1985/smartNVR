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


class EventItem(BaseModel):
    id: str
    label: str
    camera: str
    start_time: float
    end_time: float | None
    score: float | None
    has_clip: int
    has_snapshot: int
    zones: list[str]
    detector_type: str | None
    model_type: str | None


class EventListResponse(BaseModel):
    events: list[EventItem]
    total: int


class HealthResponse(BaseModel):
    status: str
    version: str
    db_connected: bool


class RecordingSegment(BaseModel):
    id: str
    camera: str
    path: str
    start_time: float
    end_time: float
    duration: float
    objects: int | None = None
    motion: int | None = None


class RecordingListResponse(BaseModel):
    segments: list[RecordingSegment]
    total: int
    camera: str
    date: str | None = None
    hour: int | None = None
