from dataclasses import dataclass

from frigate_intelligence.domain.entities.notification import Notification
from frigate_intelligence.domain.services.notifier_service import NotifierService


@dataclass
class SendNotificationRequest:
    message: str
    image_path: str | None = None
    chat_id: str | None = None
    event_id: str | None = None


@dataclass
class SendNotificationResponse:
    success: bool
    error: str | None = None


class SendNotificationUseCase:
    def __init__(self, notifier: NotifierService):
        self._notifier = notifier

    def execute(self, request: SendNotificationRequest) -> SendNotificationResponse:
        notification = Notification(
            message=request.message,
            image_path=request.image_path,
            chat_id=request.chat_id,
            event_id=request.event_id,
        )
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        success = loop.run_until_complete(self._notifier.send(notification))
        return SendNotificationResponse(
            success=success, error=None if success else "Send failed"
        )
