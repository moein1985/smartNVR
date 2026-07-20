import logging

import httpx

logger = logging.getLogger(__name__)


class BotNotificationService:
    @staticmethod
    async def send_telegram_message(
        token: str, chat_id: str, text: str
    ) -> bool:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "Markdown",
                    },
                    timeout=10.0,
                )
            if resp.status_code == 200:
                logger.info(f"Telegram message sent to chat_id={chat_id}")
                return True
            logger.warning(
                f"Telegram API returned {resp.status_code}: {resp.text}"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    @staticmethod
    async def send_bale_message(
        token: str, chat_id: str, text: str
    ) -> bool:
        url = f"https://tapi.bale.ai/bot{token}/sendMessage"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                    },
                    timeout=10.0,
                )
            if resp.status_code == 200:
                logger.info(f"Bale message sent to chat_id={chat_id}")
                return True
            logger.warning(
                f"Bale API returned {resp.status_code}: {resp.text}"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to send Bale message: {e}")
            return False
