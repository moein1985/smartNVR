import httpx

from frigate_intelligence.domain.entities.notification import Notification


class BaleNotifier:
    def __init__(self, bot_token: str, default_chat_id: str):
        self._token = bot_token
        self._default_chat_id = default_chat_id
        self._base_url = f"https://api.bale.ai/v1/bots/{bot_token}"

    async def send(self, notification: Notification) -> bool:
        try:
            chat_id = notification.chat_id or self._default_chat_id
            async with httpx.AsyncClient() as client:
                if notification.image_path:
                    with open(notification.image_path, "rb") as photo:
                        files = {"photo": photo}
                        resp = await client.post(
                            f"{self._base_url}/sendPhoto",
                            data={
                                "chat_id": chat_id,
                                "caption": notification.message,
                            },
                            files=files,
                        )
                else:
                    resp = await client.post(
                        f"{self._base_url}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": notification.message,
                        },
                    )
            return resp.status_code == 200
        except Exception:
            return False
