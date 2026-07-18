from dataclasses import dataclass

from frigate_intelligence.domain.repositories.frigate_repository import (
    FrigateRepository,
)
from frigate_intelligence.domain.repositories.pos_repository import POSRepository
from frigate_intelligence.domain.entities.event import Event
from frigate_intelligence.domain.entities.pos_transaction import POSTransaction
from frigate_intelligence.domain.value_objects.time_range import TimeRange


@dataclass
class CorrelatePOSRequest:
    transaction_id: str
    time_window_seconds: float = 30.0


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
    def __init__(
        self, frigate_repo: FrigateRepository, pos_repo: POSRepository
    ):
        self._frigate = frigate_repo
        self._pos = pos_repo

    def execute(self, request: CorrelatePOSRequest) -> CorrelatePOSResponse:
        txn = self._pos.get_transaction(request.transaction_id)
        if txn is None:
            return CorrelatePOSResponse(
                matches=[], total_events=0, error="Transaction not found"
            )

        start = txn.timestamp - request.time_window_seconds
        end = txn.timestamp + request.time_window_seconds

        sql = (
            "SELECT * FROM event WHERE start_time BETWEEN ? AND ? "
            "ORDER BY start_time ASC"
        )
        result = self._frigate.execute_sql(sql, (start, end))

        if result.error:
            return CorrelatePOSResponse(
                matches=[], total_events=0, error=result.error
            )

        events: list[Event] = []
        for row in result.rows:
            events.append(
                Event(
                    id=row[0],
                    label=row[1],
                    camera=row[2],
                    start_time=row[3],
                    end_time=row[4],
                    top_score=row[5],
                    false_positive=row[6],
                    zones=row[7],
                    has_clip=row[9],
                    has_snapshot=row[10],
                    region=row[11],
                    box=row[12],
                    area=row[13],
                    retain_indefinitely=row[14],
                    sub_label=row[15],
                    ratio=row[16],
                    score=row[18],
                    model_hash=row[19],
                    detector_type=row[20],
                    model_type=row[21],
                    data=row[22],
                )
            )

        match = CorrelationMatch(
            transaction=txn,
            events=events,
            time_range=TimeRange(start=start, end=end),
        )

        return CorrelatePOSResponse(
            matches=[match], total_events=len(events)
        )
