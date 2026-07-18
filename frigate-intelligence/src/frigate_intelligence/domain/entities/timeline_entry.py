from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TimelineEntry:
    timestamp: float
    camera: str
    source: str
    source_id: str | None
    class_type: str
    data: dict[str, Any] | None
