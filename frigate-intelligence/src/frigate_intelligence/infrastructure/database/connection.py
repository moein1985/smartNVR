import sqlite3
from pathlib import Path


def create_connection(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Frigate database not found: {db_path}")
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn
