import httpx
from datetime import datetime

from frigate_intelligence.domain.entities.pos_transaction import POSTransaction


class POSApiGateway:
    def __init__(self, api_url: str, api_key: str):
        self._url = api_url
        self._key = api_key
        self._headers = {"Authorization": f"Bearer {api_key}"}

    def get_transaction(self, transaction_id: str) -> POSTransaction | None:
        with httpx.Client() as client:
            resp = client.get(
                f"{self._url}/transactions/{transaction_id}",
                headers=self._headers,
            )
            if resp.status_code != 200:
                return None
            return self._parse_transaction(resp.json())

    def get_transactions_in_range(
        self, start_time: float, end_time: float
    ) -> list[POSTransaction]:
        with httpx.Client() as client:
            start_iso = datetime.fromtimestamp(start_time).isoformat()
            end_iso = datetime.fromtimestamp(end_time).isoformat()
            resp = client.get(
                f"{self._url}/transactions",
                params={"start": start_iso, "end": end_iso},
                headers=self._headers,
            )
            if resp.status_code != 200:
                return []
            return [self._parse_transaction(t) for t in resp.json()]

    def get_latest_transactions(self, limit: int = 10) -> list[POSTransaction]:
        with httpx.Client() as client:
            resp = client.get(
                f"{self._url}/transactions",
                params={"limit": limit},
                headers=self._headers,
            )
            if resp.status_code != 200:
                return []
            return [self._parse_transaction(t) for t in resp.json()]

    def _parse_transaction(self, data: dict) -> POSTransaction:
        return POSTransaction(
            transaction_id=data["id"],
            timestamp=data["timestamp"],
            amount=data["amount"],
            card_number_masked=data.get("card_masked", ""),
            merchant_id=data.get("merchant_id", ""),
            status=data.get("status", "unknown"),
            terminal_id=data.get("terminal_id", ""),
        )
