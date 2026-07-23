from pydantic import BaseModel


class ReportRule(BaseModel):
    id: str
    name: str
    enabled: bool = True
    zones: list[str] = []
    cameras: list[str] = []
    labels: list[str] = []
    interval_hours: int = 24
    timezone: str = "Asia/Tehran"
    destination: str = "telegram"
    chat_id: str = ""
    prompt_template: str = ""
    include_summary: bool = True
    include_raw_data: bool = False
    created_at: str = ""
    last_run: str = ""
    last_status: str = ""
