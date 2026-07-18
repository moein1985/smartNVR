from dataclasses import dataclass


@dataclass(frozen=True)
class Notification:
    message: str
    image_path: str | None = None
    chat_id: str | None = None
    event_id: str | None = None
