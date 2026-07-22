from pydantic import BaseModel


class SettingsModel(BaseModel):
    avalai_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    bale_enabled: bool = False
    bale_bot_token: str = ""
    bale_chat_id: str = ""
    report_frequency: str = "disabled"
    report_target: str = "telegram"
    report_time: str = "21:00"
    report_timezone: str = "Asia/Tehran"
