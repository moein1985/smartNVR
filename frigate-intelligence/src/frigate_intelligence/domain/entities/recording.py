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
