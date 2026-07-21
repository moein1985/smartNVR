from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    frigate_db_path: str = "/opt/frigate/config/frigate.db"
    avalai_api_key: str = ""
    avalai_base_url: str = "https://api.avalai.ir/v1"
    llm_model: str = "gemini-2.5-flash"
    max_sql_retries: int = 3
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    bale_bot_token: str = ""
    bale_chat_id: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
