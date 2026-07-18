from typing import Protocol

from frigate_intelligence.domain.entities.notification import Notification


class NotifierService(Protocol):
    def send(self, notification: Notification) -> bool:
        """Send a notification. Returns True on success."""
        ...
