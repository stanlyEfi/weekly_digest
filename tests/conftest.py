import os

import pytest


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set minimal env vars for all tests."""
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test-signing-secret")
    monkeypatch.setenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "test-creds.json")
    monkeypatch.setenv("SPREADSHEET_ID", "test-spreadsheet-id")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("DIGEST_CHANNEL_ID", "C-test-digest")
    monkeypatch.setenv("INSIGHT_CHANNEL_ID", "C-test-insight")
    monkeypatch.setenv("ADMIN_SECRET", "test-secret")
