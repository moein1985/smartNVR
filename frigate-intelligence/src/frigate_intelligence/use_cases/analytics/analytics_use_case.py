from dataclasses import dataclass

from frigate_intelligence.domain.repositories.frigate_repository import (
    FrigateRepository,
)


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
        where_clauses: list[str] = []
        params: list = []
        if request.camera:
            where_clauses.append("camera = ?")
            params.append(request.camera)
        if request.start_time:
            where_clauses.append("start_time >= ?")
            params.append(request.start_time)
        if request.end_time:
            where_clauses.append("start_time <= ?")
            params.append(request.end_time)

        where_sql = (
            " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        )

        result = self._repo.execute_sql(
            f"SELECT COUNT(*) FROM event{where_sql}", tuple(params)
        )
        total = result.rows[0][0] if result.rows else 0

        result = self._repo.execute_sql(
            f"SELECT label, COUNT(*) FROM event{where_sql} "
            f"GROUP BY label ORDER BY COUNT(*) DESC",
            tuple(params),
        )
        by_label = {r[0]: r[1] for r in result.rows}

        result = self._repo.execute_sql(
            f"SELECT CAST(strftime('%H', datetime(start_time, 'unixepoch')) "
            f"AS INT) as hour, COUNT(*) "
            f"FROM event{where_sql} GROUP BY hour ORDER BY hour",
            tuple(params),
        )
        by_hour = {r[0]: r[1] for r in result.rows}

        result = self._repo.execute_sql(
            f"SELECT camera, COUNT(*) FROM event{where_sql} GROUP BY camera",
            tuple(params),
        )
        by_camera = {r[0]: r[1] for r in result.rows}

        peak_hour = max(by_hour, key=by_hour.get) if by_hour else 0

        result = self._repo.execute_sql(
            f"SELECT COUNT(DISTINCT date(datetime(start_time, 'unixepoch'))) "
            f"FROM event{where_sql}",
            tuple(params),
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
