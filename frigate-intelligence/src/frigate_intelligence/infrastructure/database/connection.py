import sqlite3
from pathlib import Path


def create_connection(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Frigate database not found: {db_path}")
    abs_path = str(path.resolve())
    conn = sqlite3.connect(f"file:{abs_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn
