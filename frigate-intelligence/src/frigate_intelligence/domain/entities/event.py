from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Event:
    id: str
    label: str
    camera: str
    start_time: float
    end_time: float | None
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
