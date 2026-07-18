from frigate_intelligence.domain.entities.notification import Notification


class TelegramNotifier:
    def __init__(self, bot_token: str, default_chat_id: str):
        self._token = bot_token
        self._default_chat_id = default_chat_id

    async def send(self, notification: Notification) -> bool:
        try:
            from telegram import Bot

            bot = Bot(token=self._token)
            chat_id = notification.chat_id or self._default_chat_id
            if notification.image_path:
                with open(notification.image_path, "rb") as photo:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=notification.message,
                        parse_mode="Markdown",
                    )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=notification.message,
                    parse_mode="Markdown",
                )
            return True
        except Exception:
            return False
