from dataclasses import dataclass


@dataclass(frozen=True)
class TimeRange:
    start: float
    end: float

    @property
    def duration_seconds(self) -> float:
        return self.end - self.start

    def contains(self, timestamp: float) -> bool:
        return self.start <= timestamp <= self.end
