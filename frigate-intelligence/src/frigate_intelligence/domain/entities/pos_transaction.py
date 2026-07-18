from dataclasses import dataclass


@dataclass(frozen=True)
class POSTransaction:
    transaction_id: str
    timestamp: float
    amount: float
    card_number_masked: str
    merchant_id: str
    status: str
    terminal_id: str
