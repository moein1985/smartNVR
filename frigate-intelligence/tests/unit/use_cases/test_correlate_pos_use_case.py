from unittest.mock import MagicMock

from frigate_intelligence.use_cases.correlate_pos.correlate_pos_use_case import (
    CorrelatePOSUseCase,
    CorrelatePOSRequest,
)
from frigate_intelligence.domain.entities.query_result import QueryResult
from frigate_intelligence.domain.entities.pos_transaction import POSTransaction


def test_correlate_transaction_not_found():
    mock_frigate = MagicMock()
    mock_pos = MagicMock()
    mock_pos.get_transaction.return_value = None

    use_case = CorrelatePOSUseCase(mock_frigate, mock_pos)
    response = use_case.execute(
        CorrelatePOSRequest(transaction_id="nonexistent")
    )

    assert response.total_events == 0
    assert response.error == "Transaction not found"
    assert response.matches == []


def test_correlate_with_events():
    txn = POSTransaction(
        transaction_id="txn123",
        timestamp=1784386154.0,
        amount=50000.0,
        card_number_masked="****1234",
        merchant_id="m1",
        status="approved",
        terminal_id="t1",
    )
    mock_frigate = MagicMock()
    mock_frigate.execute_sql.return_value = QueryResult(
        sql="SELECT * FROM event WHERE start_time BETWEEN ? AND ?",
        columns=list(range(23)),
        rows=[],
        row_count=0,
    )
    mock_pos = MagicMock()
    mock_pos.get_transaction.return_value = txn

    use_case = CorrelatePOSUseCase(mock_frigate, mock_pos)
    response = use_case.execute(
        CorrelatePOSRequest(transaction_id="txn123", time_window_seconds=30.0)
    )

    assert response.total_events == 0
    assert len(response.matches) == 1
    assert response.matches[0].transaction.transaction_id == "txn123"
    assert response.error is None


def test_correlate_db_error():
    txn = POSTransaction(
        transaction_id="txn123",
        timestamp=1784386154.0,
        amount=50000.0,
        card_number_masked="****1234",
        merchant_id="m1",
        status="approved",
        terminal_id="t1",
    )
    mock_frigate = MagicMock()
    mock_frigate.execute_sql.return_value = QueryResult(
        sql="", columns=[], rows=[], row_count=0, error="DB locked"
    )
    mock_pos = MagicMock()
    mock_pos.get_transaction.return_value = txn

    use_case = CorrelatePOSUseCase(mock_frigate, mock_pos)
    response = use_case.execute(
        CorrelatePOSRequest(transaction_id="txn123")
    )

    assert response.error == "DB locked"
    assert response.total_events == 0
