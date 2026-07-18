import sqlite3

from frigate_intelligence.domain.entities.query_result import QueryResult
from frigate_intelligence.domain.entities.event import Event
from frigate_intelligence.domain.entities.recording import Recording
from frigate_intelligence.infrastructure.database.connection import create_connection


class FrigateSqliteGateway:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = create_connection(self._db_path)
        return self._conn

    def execute_sql(self, sql: str, params: tuple = ()) -> QueryResult:
        try:
            cur = self.conn.execute(sql, params)
            columns = (
                [desc[0] for desc in cur.description] if cur.description else []
            )
            rows = cur.fetchall()
            return QueryResult(
                sql=sql,
                columns=columns,
                rows=[tuple(r) for r in rows],
                row_count=len(rows),
            )
        except Exception as e:
            return QueryResult(
                sql=sql,
                columns=[],
                rows=[],
                row_count=0,
                error=str(e),
            )

    def get_events(
        self, camera: str | None = None, label: str | None = None
    ) -> list[Event]:
        sql = "SELECT * FROM event"
        conditions = []
        params: list = []
        if camera:
            conditions.append("camera = ?")
            params.append(camera)
        if label:
            conditions.append("label = ?")
            params.append(label)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY start_time DESC LIMIT 100"
        result = self.execute_sql(sql, tuple(params))
        if result.error:
            return []
        return [self._row_to_event(r) for r in result.rows]

    def get_recordings(self, camera: str | None = None) -> list[Recording]:
        sql = "SELECT * FROM recordings"
        params: tuple = ()
        if camera:
            sql += " WHERE camera = ?"
            params = (camera,)
        sql += " ORDER BY start_time DESC LIMIT 100"
        result = self.execute_sql(sql, params)
        if result.error:
            return []
        return [self._row_to_recording(r) for r in result.rows]

    def _row_to_event(self, row: tuple) -> Event:
        return Event(
            id=row[0],
            label=row[1],
            camera=row[2],
            start_time=row[3],
            end_time=row[4],
            top_score=row[5],
            false_positive=row[6],
            zones=row[7],
            has_clip=row[9],
            has_snapshot=row[10],
            region=row[11],
            box=row[12],
            area=row[13],
            retain_indefinitely=row[14],
            sub_label=row[15],
            ratio=row[16],
            score=row[18],
            model_hash=row[19],
            detector_type=row[20],
            model_type=row[21],
            data=row[22],
        )

    def _row_to_recording(self, row: tuple) -> Recording:
        return Recording(
            id=row[0],
            camera=row[1],
            path=row[2],
            start_time=row[3],
            end_time=row[4],
            duration=row[5],
            objects=row[6],
            motion=row[7],
            segment_size=row[8],
            dbfs=row[9],
            regions=row[10],
            motion_heatmap=row[11],
        )

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
