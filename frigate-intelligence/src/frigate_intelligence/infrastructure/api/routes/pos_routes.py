from fastapi import APIRouter
from pydantic import BaseModel

from frigate_intelligence.use_cases.correlate_pos.correlate_pos_use_case import (
    CorrelatePOSUseCase,
    CorrelatePOSRequest,
)


class CorrelateRequest(BaseModel):
    transaction_id: str
    time_window_seconds: float = 30.0


def create_pos_router(correlate_use_case: CorrelatePOSUseCase) -> APIRouter:
    router = APIRouter(prefix="/api/v1/pos", tags=["pos"])

    @router.post("/correlate")
    async def correlate(request: CorrelateRequest):
        req = CorrelatePOSRequest(
            transaction_id=request.transaction_id,
            time_window_seconds=request.time_window_seconds,
        )
        response = correlate_use_case.execute(req)
        return {
            "total_events": response.total_events,
            "matches": [
                {
                    "transaction": {
                        "id": m.transaction.transaction_id,
                        "timestamp": m.transaction.timestamp,
                        "amount": m.transaction.amount,
                        "status": m.transaction.status,
                    },
                    "events": [
                        {
                            "id": e.id,
                            "label": e.label,
                            "start_time": e.start_time,
                        }
                        for e in m.events
                    ],
                    "time_range": {
                        "start": m.time_range.start,
                        "end": m.time_range.end,
                    },
                }
                for m in response.matches
            ],
            "error": response.error,
        }

    return router
