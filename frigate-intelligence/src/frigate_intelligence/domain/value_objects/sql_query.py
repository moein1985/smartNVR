from dataclasses import dataclass


@dataclass(frozen=True)
class SQLQuery:
    raw_sql: str

    @property
    def normalized(self) -> str:
        return self.raw_sql.strip().rstrip(";")

    @property
    def is_select(self) -> bool:
        return self.normalized.upper().startswith("SELECT")

    @property
    def is_safe(self) -> bool:
        dangerous = [
            "DROP",
            "DELETE",
            "INSERT",
            "UPDATE",
            "ALTER",
            "CREATE",
            "ATTACH",
            "DETACH",
        ]
        upper = self.normalized.upper()
        return not any(f" {kw} " in f" {upper} " for kw in dangerous)
