from app.config import Settings


def test_settings_loads_from_env():
    settings = Settings()
    assert settings.slack_bot_token == "xoxb-test-token"
    assert settings.slack_signing_secret == "test-signing-secret"
    assert settings.spreadsheet_id == "test-spreadsheet-id"
    assert settings.gemini_api_key == "test-gemini-key"
    assert settings.digest_channel_id == "C-test-digest"
    assert settings.insight_channel_id == "C-test-insight"
    assert settings.admin_secret == "test-secret"


def test_settings_defaults():
    settings = Settings()
    assert settings.digest_cron_day == "fri"
    assert settings.digest_cron_hour == 18
    assert settings.digest_cron_minute == 0
