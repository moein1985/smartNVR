from typing import Protocol

from frigate_intelligence.domain.entities.pos_transaction import POSTransaction


class POSRepository(Protocol):
    def get_transaction(self, transaction_id: str) -> POSTransaction | None:
        """Get a single transaction by ID."""
        ...

    def get_transactions_in_range(
        self, start_time: float, end_time: float
    ) -> list[POSTransaction]:
        """Get all transactions within a time range."""
        ...

    def get_latest_transactions(self, limit: int = 10) -> list[POSTransaction]:
        """Get the most recent transactions."""
        ...
