from unittest.mock import MagicMock

from frigate_intelligence.use_cases.analytics.analytics_use_case import (
    AnalyticsUseCase,
    AnalyticsRequest,
)
from frigate_intelligence.domain.entities.query_result import QueryResult


def test_analytics_summary():
    mock_repo = MagicMock()
    mock_repo.execute_sql.side_effect = [
        QueryResult(sql="count", columns=["count"], rows=[(5,)], row_count=1),
        QueryResult(
            sql="by_label",
            columns=["label", "count"],
            rows=[("person", 3), ("car", 2)],
            row_count=2,
        ),
        QueryResult(
            sql="by_hour",
            columns=["hour", "count"],
            rows=[(10, 2), (14, 3)],
            row_count=2,
        ),
        QueryResult(
            sql="by_camera",
            columns=["camera", "count"],
            rows=[("cam1", 5)],
            row_count=1,
        ),
        QueryResult(
            sql="distinct_days",
            columns=["days"],
            rows=[(2,)],
            row_count=1,
        ),
    ]

    use_case = AnalyticsUseCase(mock_repo)
    response = use_case.execute(AnalyticsRequest())

    assert response.total_events == 5
    assert response.events_by_label == {"person": 3, "car": 2}
    assert response.events_by_hour == {10: 2, 14: 3}
    assert response.events_by_camera == {"cam1": 5}
    assert response.peak_hour == 14
    assert response.avg_daily_events == 2.5


def test_analytics_with_camera_filter():
    mock_repo = MagicMock()
    mock_repo.execute_sql.side_effect = [
        QueryResult(sql="count", columns=["count"], rows=[(0,)], row_count=1),
        QueryResult(sql="by_label", columns=["label", "count"], rows=[], row_count=0),
        QueryResult(sql="by_hour", columns=["hour", "count"], rows=[], row_count=0),
        QueryResult(sql="by_camera", columns=["camera", "count"], rows=[], row_count=0),
        QueryResult(sql="distinct_days", columns=["days"], rows=[(1,)], row_count=1),
    ]

    use_case = AnalyticsUseCase(mock_repo)
    response = use_case.execute(AnalyticsRequest(camera="cam2"))

    assert response.total_events == 0
    assert response.peak_hour == 0
