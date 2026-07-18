from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReviewSegment:
    id: str
    camera: str
    start_time: float
    end_time: float | None
    severity: str
    thumb_path: str
    data: dict[str, Any]
