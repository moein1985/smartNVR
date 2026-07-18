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
