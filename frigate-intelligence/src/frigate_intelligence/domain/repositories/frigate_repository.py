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
