import re

VALID_TABLES = {
    "event",
    "recordings",
    "timeline",
    "reviewsegment",
    "previews",
    "regions",
    "user",
    "export",
    "exportcase",
    "migratehistory",
    "trigger",
    "userreviewstatus",
    "sqlite_sequence",
}


class SQLValidator:
    @staticmethod
    def validate(sql: str) -> tuple[bool, str | None]:
        sql_stripped = sql.strip().rstrip(";").strip()

        if not sql_stripped:
            return False, "Empty SQL"

        if not sql_stripped.upper().startswith("SELECT"):
            return False, "Only SELECT queries are allowed"

        dangerous_patterns = [
            "DROP",
            "DELETE",
            "INSERT",
            "UPDATE",
            "ALTER",
            "CREATE",
            "ATTACH",
            "DETACH",
            "PRAGMA",
            "VACUUM",
        ]
        upper = sql_stripped.upper()
        for pattern in dangerous_patterns:
            if re.search(rf"\b{pattern}\b", upper):
                return False, f"Dangerous keyword detected: {pattern}"

        if not any(table in sql_stripped.lower() for table in VALID_TABLES):
            return False, "No valid table name found in query"

        return True, None
