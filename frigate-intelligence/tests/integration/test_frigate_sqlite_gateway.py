import sqlite3
import tempfile
import os

from frigate_intelligence.infrastructure.database.frigate_sqlite_gateway import (
    FrigateSqliteGateway,
)


def test_execute_sql_on_real_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE event (id TEXT, label TEXT, camera TEXT, start_time REAL)"
    )
    conn.execute(
        "INSERT INTO event VALUES ('1', 'person', 'cam1', 1784386154.0)"
    )
    conn.commit()
    conn.close()

    try:
        gateway = FrigateSqliteGateway(db_path)
        result = gateway.execute_sql("SELECT * FROM event")
        assert result.is_success
        assert result.row_count == 1
        assert result.columns == ["id", "label", "camera", "start_time"]
        gateway.close()
    finally:
        os.unlink(db_path)


def test_execute_sql_error_handling():
    gateway = FrigateSqliteGateway("/nonexistent/path.db")
    result = gateway.execute_sql("SELECT * FROM event")
    assert not result.is_success
    assert result.error is not None
