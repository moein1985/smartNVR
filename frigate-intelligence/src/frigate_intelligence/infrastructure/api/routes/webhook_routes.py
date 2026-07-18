from fastapi import APIRouter, Request

from frigate_intelligence.use_cases.send_notification.send_notification_use_case import (
    SendNotificationUseCase,
    SendNotificationRequest,
)
from frigate_intelligence.interface_adapters.presenters.bot_presenter import (
    BotPresenter,
)


def create_webhook_router(
    notification_use_case: SendNotificationUseCase,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

    @router.post("/frigate")
    async def frigate_webhook(request: Request):
        payload = await request.json()
        event_type = payload.get("type", "")
        event_data = payload.get("payload", {})

        if event_type == "new":
            alert_text = BotPresenter.to_alert(event_data)
            notification_req = SendNotificationRequest(
                message=alert_text,
                event_id=event_data.get("id"),
            )
            notification_use_case.execute(notification_req)

        return {"status": "ok"}

    return router
