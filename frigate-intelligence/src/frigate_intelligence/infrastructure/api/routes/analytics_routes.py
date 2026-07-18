from fastapi import APIRouter, Query

from frigate_intelligence.use_cases.analytics.analytics_use_case import (
    AnalyticsUseCase,
    AnalyticsRequest,
)


def create_analytics_router(analytics_use_case: AnalyticsUseCase) -> APIRouter:
    router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

    @router.get("/summary")
    async def summary(
        camera: str | None = Query(None),
        start_time: float | None = Query(None),
        end_time: float | None = Query(None),
    ):
        req = AnalyticsRequest(
            camera=camera, start_time=start_time, end_time=end_time
        )
        resp = analytics_use_case.execute(req)
        return {
            "total_events": resp.total_events,
            "events_by_label": resp.events_by_label,
            "events_by_hour": resp.events_by_hour,
            "events_by_camera": resp.events_by_camera,
            "peak_hour": resp.peak_hour,
            "avg_daily_events": resp.avg_daily_events,
        }

    return router
