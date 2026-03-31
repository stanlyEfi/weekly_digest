from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    slack_bot_token: str
    slack_signing_secret: str
    google_sheets_credentials_file: str
    spreadsheet_id: str
    gemini_api_key: str
    digest_channel_id: str
    admin_secret: str
    digest_cron_day: str = "fri"
    digest_cron_hour: int = 18
    digest_cron_minute: int = 0

    model_config = {"env_file": ".env"}
