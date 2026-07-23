import logging

from frigate_intelligence.domain.entities.notification import Notification
from frigate_intelligence.infrastructure.notifiers.telegram_notifier import (
    TelegramNotifier,
)
from frigate_intelligence.infrastructure.notifiers.bale_notifier import BaleNotifier

logger = logging.getLogger(__name__)


class NotifierFactory:
    def __init__(
        self,
        telegram_bot_token: str = "",
        telegram_chat_id: str = "",
        bale_bot_token: str = "",
        bale_chat_id: str = "",
    ) -> None:
        self._telegram_bot_token = telegram_bot_token
        self._telegram_chat_id = telegram_chat_id
        self._bale_bot_token = bale_bot_token
        self._bale_chat_id = bale_chat_id

    def create(self, destination: str):
        if destination == "telegram":
            if not self._telegram_bot_token:
                logger.warning("[NotifierFactory] Telegram bot token is empty")
            return TelegramNotifier(
                bot_token=self._telegram_bot_token,
                default_chat_id=self._telegram_chat_id,
            )
        elif destination == "bale":
            if not self._bale_bot_token:
                logger.warning("[NotifierFactory] Bale bot token is empty")
            return BaleNotifier(
                bot_token=self._bale_bot_token,
                default_chat_id=self._bale_chat_id,
            )
        else:
            logger.error(
                "[NotifierFactory] Unknown destination '%s', defaulting to telegram",
                destination,
            )
            return TelegramNotifier(
                bot_token=self._telegram_bot_token,
                default_chat_id=self._telegram_chat_id,
            )

    async def send(
        self,
        destination: str,
        notification: Notification,
        chat_id: str = "",
    ) -> bool:
        notifier = self.create(destination)
        if chat_id:
            notification = Notification(
                message=notification.message,
                image_path=notification.image_path,
                chat_id=chat_id,
                event_id=notification.event_id,
            )
        try:
            success = await notifier.send(notification)
            if success:
                logger.info(
                    "[NotifierFactory] Sent to %s successfully",
                    destination,
                )
            else:
                logger.warning(
                    "[NotifierFactory] Send to %s returned False",
                    destination,
                )
            return success
        except Exception as e:
            logger.error(
                "[NotifierFactory] Send to %s failed: %s",
                destination,
                e,
                exc_info=True,
            )
            return False
