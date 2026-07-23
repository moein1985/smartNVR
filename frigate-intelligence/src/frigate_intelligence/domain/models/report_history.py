from pydantic import BaseModel


class ReportHistoryEntry(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    executed_at: str
    status: str
    message_preview: str = ""
    destination: str = ""
