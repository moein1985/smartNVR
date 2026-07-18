from fastapi import APIRouter, Query

from frigate_intelligence.interface_adapters.schemas.api_models import (
    EventListResponse,
    EventItem,
)


def create_event_router(frigate_repo) -> APIRouter:
    router = APIRouter(prefix="/api/v1/events", tags=["events"])

    @router.get("", response_model=EventListResponse)
    async def list_events(
        camera: str | None = Query(None),
        label: str | None = Query(None),
    ):
        events = frigate_repo.get_events(camera=camera, label=label)
        items = [
            EventItem(
                id=e.id,
                label=e.label,
                camera=e.camera,
                start_time=e.start_time,
                end_time=e.end_time,
                score=e.score,
                has_clip=e.has_clip,
                has_snapshot=e.has_snapshot,
                zones=e.zones,
                detector_type=e.detector_type,
                model_type=e.model_type,
            )
            for e in events
        ]
        return EventListResponse(events=items, total=len(items))

    return router
