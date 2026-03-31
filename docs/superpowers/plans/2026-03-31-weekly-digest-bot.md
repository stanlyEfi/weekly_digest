# Weekly Digest Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI service that collects team insights from Slack into Google Sheets and generates a weekly digest via Gemini API.

**Architecture:** Single FastAPI process with APScheduler. Slack Events API webhook for inbound messages, Google Sheets for storage, Gemini for summarization. Deployed as Docker container behind nginx on a DO droplet.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, APScheduler, slack-sdk, google-api-python-client, google-generativeai, pydantic-settings, pytest, Docker.

---

## File Map

| File | Responsibility |
|------|---------------|
| `app/__init__.py` | Package marker |
| `app/config.py` | Pydantic settings loaded from `.env` |
| `app/slack_client.py` | Slack Web API wrapper: `get_user_info`, `add_reaction`, `post_message` |
| `app/sheets_client.py` | Google Sheets: `append_row`, `get_all_rows` |
| `app/gemini_client.py` | Gemini API: `generate_summary` |
| `app/slack_handler.py` | Slack event processing: signature verification, message handling |
| `app/digest_generator.py` | Digest orchestration: read sheets, filter, aggregate, call Gemini, post |
| `app/main.py` | FastAPI app, routes, lifespan with APScheduler |
| `tests/conftest.py` | Shared fixtures |
| `tests/test_config.py` | Config loading tests |
| `tests/test_slack_client.py` | Slack client tests |
| `tests/test_sheets_client.py` | Sheets client tests |
| `tests/test_gemini_client.py` | Gemini client tests |
| `tests/test_slack_handler.py` | Slack event handler tests |
| `tests/test_digest_generator.py` | Digest generation tests |
| `tests/test_main.py` | Integration tests for endpoints |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for environment variables |
| `Dockerfile` | Container build |
| `docker-compose.yml` | Container orchestration |

---

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi==0.115.12
uvicorn==0.34.2
apscheduler==3.11.0
slack-sdk==3.35.1
google-api-python-client==2.170.0
google-auth==2.40.1
google-generativeai==0.8.5
pydantic-settings==2.9.1
pytest==8.3.5
httpx==0.28.1
```

- [ ] **Step 2: Create `.env.example`**

```
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-signing-secret
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
SPREADSHEET_ID=1xRhhDxFughUBHxEO98aktxgtUX5yeOK76Yz8rIQBOe4
GEMINI_API_KEY=your-gemini-key
DIGEST_CHANNEL_ID=C044KE0U4QG
INSIGHT_CHANNEL_ID=C-your-insight-channel
ADMIN_SECRET=your-admin-secret
DIGEST_CRON_DAY=fri
DIGEST_CRON_HOUR=18
DIGEST_CRON_MINUTE=0
```

- [ ] **Step 3: Create `app/__init__.py`**

Empty file.

- [ ] **Step 4: Write failing test for config**

Create `tests/__init__.py` (empty) and `tests/conftest.py`:

```python
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
```

Create `tests/test_config.py`:

```python
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
```

- [ ] **Step 5: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.config'`

- [ ] **Step 6: Implement `app/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    slack_bot_token: str
    slack_signing_secret: str
    google_sheets_credentials_file: str
    spreadsheet_id: str
    gemini_api_key: str
    digest_channel_id: str
    insight_channel_id: str
    admin_secret: str
    digest_cron_day: str = "fri"
    digest_cron_hour: int = 18
    digest_cron_minute: int = 0

    model_config = {"env_file": ".env"}
```

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: 2 passed

- [ ] **Step 8: Commit**

```bash
git add app/ tests/ requirements.txt .env.example
git commit -m "feat: project scaffold with config and tests"
```

---

### Task 2: Slack Client

**Files:**
- Create: `app/slack_client.py`
- Create: `tests/test_slack_client.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_slack_client.py`:

```python
from unittest.mock import MagicMock, patch

from app.slack_client import SlackClient


def test_get_user_info_returns_name_and_title():
    mock_client = MagicMock()
    mock_client.users_info.return_value = {
        "ok": True,
        "user": {
            "is_bot": False,
            "profile": {
                "real_name": "Stan Gulevich",
                "title": "Head of Product",
            },
        },
    }

    client = SlackClient.__new__(SlackClient)
    client.client = mock_client

    info = client.get_user_info("UF5107WSV")
    assert info["real_name"] == "Stan Gulevich"
    assert info["title"] == "Head of Product"
    assert info["is_bot"] is False


def test_get_user_info_fallback_on_error():
    mock_client = MagicMock()
    mock_client.users_info.side_effect = Exception("Slack API error")

    client = SlackClient.__new__(SlackClient)
    client.client = mock_client

    info = client.get_user_info("U-unknown")
    assert info["real_name"] == "U-unknown"
    assert info["title"] == ""
    assert info["is_bot"] is False


def test_add_reaction():
    mock_client = MagicMock()
    mock_client.reactions_add.return_value = {"ok": True}

    client = SlackClient.__new__(SlackClient)
    client.client = mock_client

    client.add_reaction("C-channel", "1234567890.123456", "+1")
    mock_client.reactions_add.assert_called_once_with(
        channel="C-channel", timestamp="1234567890.123456", name="+1"
    )


def test_post_message():
    mock_client = MagicMock()
    mock_client.chat_postMessage.return_value = {"ok": True}

    client = SlackClient.__new__(SlackClient)
    client.client = mock_client

    client.post_message("C-channel", "Hello")
    mock_client.chat_postMessage.assert_called_once_with(
        channel="C-channel", text="Hello", mrkdwn=True, unfurl_links=False
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_slack_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.slack_client'`

- [ ] **Step 3: Implement `app/slack_client.py`**

```python
import logging

from slack_sdk import WebClient

logger = logging.getLogger(__name__)


class SlackClient:
    def __init__(self, token: str):
        self.client = WebClient(token=token)

    def get_user_info(self, user_id: str) -> dict:
        try:
            response = self.client.users_info(user=user_id)
            user = response["user"]
            return {
                "real_name": user["profile"].get("real_name", user_id),
                "title": user["profile"].get("title", ""),
                "is_bot": user.get("is_bot", False),
            }
        except Exception:
            logger.exception("Failed to get user info for %s", user_id)
            return {"real_name": user_id, "title": "", "is_bot": False}

    def add_reaction(self, channel: str, timestamp: str, name: str) -> None:
        try:
            self.client.reactions_add(
                channel=channel, timestamp=timestamp, name=name
            )
        except Exception:
            logger.exception("Failed to add reaction")

    def post_message(self, channel: str, text: str) -> None:
        try:
            self.client.chat_postMessage(
                channel=channel, text=text, mrkdwn=True, unfurl_links=False
            )
        except Exception:
            logger.exception("Failed to post message to %s", channel)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_slack_client.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/slack_client.py tests/test_slack_client.py
git commit -m "feat: Slack client with user info, reactions, and posting"
```

---

### Task 3: Google Sheets Client

**Files:**
- Create: `app/sheets_client.py`
- Create: `tests/test_sheets_client.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_sheets_client.py`:

```python
from unittest.mock import MagicMock, patch

from app.sheets_client import SheetsClient


def _make_client(mock_service):
    client = SheetsClient.__new__(SheetsClient)
    client.service = mock_service
    client.spreadsheet_id = "test-spreadsheet-id"
    return client


def test_append_row():
    mock_service = MagicMock()
    mock_append = mock_service.spreadsheets().values().append
    mock_append.return_value.execute.return_value = {"updates": {"updatedRows": 1}}

    client = _make_client(mock_service)

    row = {
        "user_id": "U123",
        "username": "Stan",
        "role": "PM",
        "text": "Launched feature X",
        "timestamp": "2026-03-31T10:00:00",
        "ts": "1234567890.123456",
        "channel": "C-insight",
        "week_number": 14,
    }

    client.append_row(row)
    mock_append.assert_called_once()


def test_get_all_rows():
    mock_service = MagicMock()
    mock_get = mock_service.spreadsheets().values().get
    mock_get.return_value.execute.return_value = {
        "values": [
            ["user_id", "username", "role", "text", "timestamp", "ts", "channel", "week_number"],
            ["U123", "Stan", "PM", "Launched feature X", "2026-03-31T10:00:00", "123.456", "C-ch", "14"],
            ["U456", "Kirill", "CEO", "Revenue grew 20%", "2026-03-30T09:00:00", "789.012", "C-ch", "14"],
        ]
    }

    client = _make_client(mock_service)

    rows = client.get_all_rows()
    assert len(rows) == 2
    assert rows[0]["username"] == "Stan"
    assert rows[1]["text"] == "Revenue grew 20%"


def test_get_all_rows_empty_sheet():
    mock_service = MagicMock()
    mock_get = mock_service.spreadsheets().values().get
    mock_get.return_value.execute.return_value = {}

    client = _make_client(mock_service)

    rows = client.get_all_rows()
    assert rows == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_sheets_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.sheets_client'`

- [ ] **Step 3: Implement `app/sheets_client.py`**

```python
import logging

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "Messages"
COLUMNS = ["user_id", "username", "role", "text", "timestamp", "ts", "channel", "week_number"]


class SheetsClient:
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        self.service = build("sheets", "v4", credentials=creds)
        self.spreadsheet_id = spreadsheet_id

    def append_row(self, row: dict) -> None:
        values = [[row.get(col, "") for col in COLUMNS]]
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{SHEET_NAME}!A:H",
            valueInputOption="USER_ENTERED",
            body={"values": values},
        ).execute()

    def get_all_rows(self) -> list[dict]:
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=f"{SHEET_NAME}!A:H")
            .execute()
        )
        values = result.get("values", [])
        if len(values) < 2:
            return []
        headers = values[0]
        return [dict(zip(headers, row)) for row in values[1:]]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_sheets_client.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/sheets_client.py tests/test_sheets_client.py
git commit -m "feat: Google Sheets client for read/write operations"
```

---

### Task 4: Gemini Client

**Files:**
- Create: `app/gemini_client.py`
- Create: `tests/test_gemini_client.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_gemini_client.py`:

```python
from unittest.mock import MagicMock, patch

from app.gemini_client import GeminiClient

SYSTEM_PROMPT = (
    "Ты — ассистент продуктовой команды. Твоя задача — создавать структурированные "
    "еженедельные дайджесты на основе инсайтов от разных людей и команд. Новости можно "
    "разделять по командам, либо компоновать по смыслу. Важно: формат ответа без "
    "приветствий, сразу дайджест. Форматирование должно быть адаптировано для Slack, не md."
)


def test_generate_summary_returns_text():
    mock_model = MagicMock()
    mock_model.generate_content.return_value.text = "*Product*\n• Launched feature X"

    client = GeminiClient.__new__(GeminiClient)
    client.model = mock_model

    result = client.generate_summary("1. [Stan/PM] Launched feature X")
    assert "*Product*" in result
    mock_model.generate_content.assert_called_once()


def test_generate_summary_returns_none_on_error():
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("API error")

    client = GeminiClient.__new__(GeminiClient)
    client.model = mock_model

    result = client.generate_summary("1. [Stan/PM] Launched feature X")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gemini_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.gemini_client'`

- [ ] **Step 3: Implement `app/gemini_client.py`**

```python
import logging

import google.generativeai as genai

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты — ассистент продуктовой команды. Твоя задача — создавать структурированные "
    "еженедельные дайджесты на основе инсайтов от разных людей и команд. Новости можно "
    "разделять по командам, либо компоновать по смыслу. Важно: формат ответа без "
    "приветствий, сразу дайджест. Форматирование должно быть адаптировано для Slack, не md."
)


class GeminiClient:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",
            system_instruction=SYSTEM_PROMPT,
        )

    def generate_summary(self, insights_text: str) -> str | None:
        try:
            response = self.model.generate_content(
                f"Вот инсайты за эту неделю:\n\n{insights_text}\n\nСоздай структурированный дайджест."
            )
            return response.text
        except Exception:
            logger.exception("Failed to generate summary via Gemini")
            return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_gemini_client.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/gemini_client.py tests/test_gemini_client.py
git commit -m "feat: Gemini client for digest summary generation"
```

---

### Task 5: Slack Event Handler

**Files:**
- Create: `app/slack_handler.py`
- Create: `tests/test_slack_handler.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_slack_handler.py`:

```python
import hashlib
import hmac
import time
from unittest.mock import MagicMock

from app.slack_handler import verify_slack_signature, process_message


def test_verify_signature_valid():
    secret = "test-signing-secret"
    timestamp = str(int(time.time()))
    body = b'{"type":"event_callback"}'
    sig_basestring = f"v0:{timestamp}:{body.decode()}".encode()
    expected_sig = "v0=" + hmac.new(
        secret.encode(), sig_basestring, hashlib.sha256
    ).hexdigest()

    assert verify_slack_signature(secret, body, timestamp, expected_sig) is True


def test_verify_signature_invalid():
    assert verify_slack_signature("secret", b"body", "123", "v0=bad") is False


def test_verify_signature_too_old():
    secret = "test-signing-secret"
    timestamp = str(int(time.time()) - 600)
    body = b'{"type":"event_callback"}'
    sig_basestring = f"v0:{timestamp}:{body.decode()}".encode()
    sig = "v0=" + hmac.new(
        secret.encode(), sig_basestring, hashlib.sha256
    ).hexdigest()

    assert verify_slack_signature(secret, body, timestamp, sig) is False


def test_process_message_saves_and_reacts():
    slack_client = MagicMock()
    slack_client.get_user_info.return_value = {
        "real_name": "Stan",
        "title": "PM",
        "is_bot": False,
    }
    sheets_client = MagicMock()

    event = {
        "user": "U123",
        "text": "Launched feature X",
        "ts": "1234567890.123456",
        "channel": "C-insight",
    }

    process_message(event, slack_client, sheets_client, digest_channel_id="C-digest")

    sheets_client.append_row.assert_called_once()
    row = sheets_client.append_row.call_args[0][0]
    assert row["username"] == "Stan"
    assert row["role"] == "PM"
    assert row["text"] == "Launched feature X"

    slack_client.add_reaction.assert_called_once_with(
        "C-insight", "1234567890.123456", "+1"
    )


def test_process_message_skips_bot():
    slack_client = MagicMock()
    slack_client.get_user_info.return_value = {
        "real_name": "Bot",
        "title": "",
        "is_bot": True,
    }
    sheets_client = MagicMock()

    event = {
        "user": "U-bot",
        "text": "automated message",
        "ts": "123.456",
        "channel": "C-insight",
    }

    process_message(event, slack_client, sheets_client, digest_channel_id="C-digest")

    sheets_client.append_row.assert_not_called()
    slack_client.add_reaction.assert_not_called()


def test_process_message_skips_empty_text():
    slack_client = MagicMock()
    sheets_client = MagicMock()

    event = {
        "user": "U123",
        "text": "",
        "ts": "123.456",
        "channel": "C-insight",
    }

    process_message(event, slack_client, sheets_client, digest_channel_id="C-digest")

    slack_client.get_user_info.assert_not_called()
    sheets_client.append_row.assert_not_called()


def test_process_message_skips_digest_channel():
    slack_client = MagicMock()
    sheets_client = MagicMock()

    event = {
        "user": "U123",
        "text": "some text",
        "ts": "123.456",
        "channel": "C-digest",
    }

    process_message(event, slack_client, sheets_client, digest_channel_id="C-digest")

    slack_client.get_user_info.assert_not_called()
    sheets_client.append_row.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_slack_handler.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.slack_handler'`

- [ ] **Step 3: Implement `app/slack_handler.py`**

```python
import hashlib
import hmac
import logging
import time
from datetime import datetime, timezone

from app.sheets_client import SheetsClient
from app.slack_client import SlackClient

logger = logging.getLogger(__name__)


def verify_slack_signature(
    signing_secret: str, body: bytes, timestamp: str, signature: str
) -> bool:
    try:
        ts = int(timestamp)
    except (ValueError, TypeError):
        return False

    if abs(time.time() - ts) > 300:
        return False

    sig_basestring = f"v0:{timestamp}:{body.decode()}".encode()
    expected = "v0=" + hmac.new(
        signing_secret.encode(), sig_basestring, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def _get_week_number(dt: datetime) -> int:
    return dt.isocalendar()[1]


def process_message(
    event: dict,
    slack_client: SlackClient,
    sheets_client: SheetsClient,
    digest_channel_id: str,
) -> None:
    text = event.get("text", "")
    channel = event.get("channel", "")
    user_id = event.get("user", "")
    ts = event.get("ts", "")

    if not text or not text.strip():
        return

    if channel == digest_channel_id:
        return

    user_info = slack_client.get_user_info(user_id)

    if user_info["is_bot"]:
        return

    now = datetime.now(timezone.utc)

    row = {
        "user_id": user_id,
        "username": user_info["real_name"],
        "role": user_info["title"],
        "text": text,
        "timestamp": now.isoformat(),
        "ts": ts,
        "channel": channel,
        "week_number": _get_week_number(now),
    }

    try:
        sheets_client.append_row(row)
        slack_client.add_reaction(channel, ts, "+1")
    except Exception:
        logger.exception("Failed to save message from %s", user_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_slack_handler.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add app/slack_handler.py tests/test_slack_handler.py
git commit -m "feat: Slack event handler with signature verification and message processing"
```

---

### Task 6: Digest Generator

**Files:**
- Create: `app/digest_generator.py`
- Create: `tests/test_digest_generator.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_digest_generator.py`:

```python
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.digest_generator import filter_recent, aggregate_insights, format_message, generate_digest


def test_filter_recent_keeps_last_7_days():
    now = datetime.now(timezone.utc)
    rows = [
        {"timestamp": (now - timedelta(days=1)).isoformat(), "username": "A", "text": "x"},
        {"timestamp": (now - timedelta(days=3)).isoformat(), "username": "B", "text": "y"},
        {"timestamp": (now - timedelta(days=10)).isoformat(), "username": "C", "text": "z"},
    ]
    result = filter_recent(rows)
    assert len(result) == 2
    assert result[0]["username"] == "A"
    assert result[1]["username"] == "B"


def test_filter_recent_empty():
    assert filter_recent([]) == []


def test_aggregate_insights():
    rows = [
        {"username": "Stan", "role": "PM", "text": "Launched feature X"},
        {"username": "Stan", "role": "PM", "text": "Fixed bug Y"},
        {"username": "Kirill", "role": "CEO", "text": "Revenue grew 20%"},
    ]
    insights_text, stats_text, total = aggregate_insights(rows)

    assert "1. [Stan/PM] Launched feature X" in insights_text
    assert "2. [Stan/PM] Fixed bug Y" in insights_text
    assert "3. [Kirill/CEO] Revenue grew 20%" in insights_text
    assert total == 3
    assert "Stan: 2 (67%)" in stats_text
    assert "Kirill: 1 (33%)" in stats_text


def test_format_message_with_summary():
    message = format_message(
        summary="*Product*\n• Launched feature X",
        stats_text="• Stan: 2 (67%)\n• Kirill: 1 (33%)",
        total=3,
    )
    assert "*Product*" in message
    assert "Stan: 2 (67%)" in message
    assert "3" in message


def test_format_message_without_summary():
    message = format_message(
        summary=None,
        stats_text="• Stan: 1 (100%)",
        total=1,
        raw_insights="1. [Stan/PM] Launched feature X",
    )
    assert "1. [Stan/PM] Launched feature X" in message
    assert "Stan: 1 (100%)" in message


def test_generate_digest_posts_summary():
    sheets_client = MagicMock()
    now = datetime.now(timezone.utc)
    sheets_client.get_all_rows.return_value = [
        {
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "username": "Stan",
            "role": "PM",
            "text": "Launched feature X",
        },
    ]

    gemini_client = MagicMock()
    gemini_client.generate_summary.return_value = "*Product*\n• Launched feature X"

    slack_client = MagicMock()

    generate_digest(sheets_client, gemini_client, slack_client, "C-digest")

    slack_client.post_message.assert_called_once()
    posted_text = slack_client.post_message.call_args[0][1]
    assert "*Product*" in posted_text


def test_generate_digest_no_insights():
    sheets_client = MagicMock()
    sheets_client.get_all_rows.return_value = []

    gemini_client = MagicMock()
    slack_client = MagicMock()

    generate_digest(sheets_client, gemini_client, slack_client, "C-digest")

    slack_client.post_message.assert_called_once()
    posted_text = slack_client.post_message.call_args[0][1]
    assert "инсайтов не было" in posted_text
    gemini_client.generate_summary.assert_not_called()


def test_generate_digest_gemini_fails_posts_raw():
    sheets_client = MagicMock()
    now = datetime.now(timezone.utc)
    sheets_client.get_all_rows.return_value = [
        {
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "username": "Stan",
            "role": "PM",
            "text": "Launched feature X",
        },
    ]

    gemini_client = MagicMock()
    gemini_client.generate_summary.return_value = None

    slack_client = MagicMock()

    generate_digest(sheets_client, gemini_client, slack_client, "C-digest")

    slack_client.post_message.assert_called_once()
    posted_text = slack_client.post_message.call_args[0][1]
    assert "[Stan/PM] Launched feature X" in posted_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_digest_generator.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.digest_generator'`

- [ ] **Step 3: Implement `app/digest_generator.py`**

```python
import logging
import math
from datetime import datetime, timedelta, timezone

from app.gemini_client import GeminiClient
from app.sheets_client import SheetsClient
from app.slack_client import SlackClient

logger = logging.getLogger(__name__)

NO_INSIGHTS_MESSAGE = (
    "На этой неделе инсайтов не было. Не забывайте делиться обновлениями!"
)


def filter_recent(rows: list[dict], days: int = 7) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = []
    for row in rows:
        try:
            ts = datetime.fromisoformat(row["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts > cutoff:
                result.append(row)
        except (ValueError, KeyError):
            continue
    return result


def aggregate_insights(rows: list[dict]) -> tuple[str, str, int]:
    total = len(rows)
    insights_lines = []
    user_counts: dict[str, int] = {}

    for i, row in enumerate(rows, 1):
        username = row.get("username", "Unknown")
        role = row.get("role", "")
        text = row.get("text", "")
        insights_lines.append(f"{i}. [{username}/{role}] {text}")
        user_counts[username] = user_counts.get(username, 0) + 1

    insights_text = "\n".join(insights_lines)

    stats_entries = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
    stats_lines = [
        f"• {user}: {count} ({round(count / total * 100)}%)"
        for user, count in stats_entries
    ]
    stats_text = "\n".join(stats_lines)

    return insights_text, stats_text, total


def format_message(
    summary: str | None,
    stats_text: str,
    total: int,
    raw_insights: str | None = None,
) -> str:
    body = summary if summary else raw_insights
    return (
        f"{body}\n\n"
        f"---\n\n"
        f":bar_chart: *Статистика сообщений за неделю ({total}):*\n"
        f"{stats_text}\n\n"
        f":robot_face: Всем отличных выходных! :crezu-heart:"
    )


def generate_digest(
    sheets_client: SheetsClient,
    gemini_client: GeminiClient,
    slack_client: SlackClient,
    digest_channel_id: str,
) -> None:
    try:
        all_rows = sheets_client.get_all_rows()
    except Exception:
        logger.exception("Failed to read from Google Sheets")
        return

    recent = filter_recent(all_rows)

    if not recent:
        slack_client.post_message(digest_channel_id, NO_INSIGHTS_MESSAGE)
        return

    insights_text, stats_text, total = aggregate_insights(recent)

    summary = gemini_client.generate_summary(insights_text)

    message = format_message(
        summary=summary,
        stats_text=stats_text,
        total=total,
        raw_insights=insights_text,
    )

    slack_client.post_message(digest_channel_id, message)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_digest_generator.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add app/digest_generator.py tests/test_digest_generator.py
git commit -m "feat: digest generator with filtering, aggregation, and Gemini summary"
```

---

### Task 7: FastAPI App and Routes

**Files:**
- Create: `app/main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_main.py`:

```python
import hashlib
import hmac
import json
import time
from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app


@pytest.fixture
def app():
    with patch("app.main.SheetsClient"), \
         patch("app.main.SlackClient"), \
         patch("app.main.GeminiClient"):
        yield create_app()


@pytest.mark.anyio
async def test_health(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_slack_url_verification(app):
    body = json.dumps({"type": "url_verification", "challenge": "test-challenge"})
    timestamp = str(int(time.time()))
    sig = _sign(body, timestamp)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/slack/events",
            content=body,
            headers={
                "X-Slack-Request-Timestamp": timestamp,
                "X-Slack-Signature": sig,
                "Content-Type": "application/json",
            },
        )
    assert response.status_code == 200
    assert response.json()["challenge"] == "test-challenge"


@pytest.mark.anyio
async def test_slack_events_invalid_signature(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/slack/events",
            content=b'{"type":"event_callback"}',
            headers={
                "X-Slack-Request-Timestamp": str(int(time.time())),
                "X-Slack-Signature": "v0=invalid",
                "Content-Type": "application/json",
            },
        )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_digest_generate_requires_auth(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/digest/generate")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_digest_generate_with_auth(app):
    with patch("app.main.generate_digest"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/digest/generate",
                headers={"Authorization": "Bearer test-secret"},
            )
    assert response.status_code == 200


def _sign(body: str, timestamp: str) -> str:
    sig_basestring = f"v0:{timestamp}:{body}".encode()
    return "v0=" + hmac.new(
        b"test-signing-secret", sig_basestring, hashlib.sha256
    ).hexdigest()
```

- [ ] **Step 2: Add `anyio` and `pytest-anyio` to `requirements.txt`**

Append to `requirements.txt`:

```
anyio==4.9.0
pytest-anyio==0.0.0
```

Note: `pytest-anyio` is actually `anyio` with `pytest` — use `pytest.ini` or add to `conftest.py`:

Add to `tests/conftest.py`:

```python
@pytest.fixture
def anyio_backend():
    return "asyncio"
```

Actually, use `httpx` with `ASGITransport` which is already in requirements. Replace `pytest-anyio` with `pytest-asyncio`:

Append to `requirements.txt`:

```
pytest-asyncio==0.25.3
```

Update `tests/test_main.py` — replace `@pytest.mark.anyio` with `@pytest.mark.asyncio` everywhere. Remove the `anyio_backend` fixture.

Updated `tests/test_main.py`:

```python
import hashlib
import hmac
import json
import time
from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app


@pytest.fixture
def app():
    with patch("app.main.SheetsClient"), \
         patch("app.main.SlackClient"), \
         patch("app.main.GeminiClient"):
        yield create_app()


@pytest.mark.asyncio
async def test_health(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_slack_url_verification(app):
    body = json.dumps({"type": "url_verification", "challenge": "test-challenge"})
    timestamp = str(int(time.time()))
    sig = _sign(body, timestamp)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/slack/events",
            content=body,
            headers={
                "X-Slack-Request-Timestamp": timestamp,
                "X-Slack-Signature": sig,
                "Content-Type": "application/json",
            },
        )
    assert response.status_code == 200
    assert response.json()["challenge"] == "test-challenge"


@pytest.mark.asyncio
async def test_slack_events_invalid_signature(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/slack/events",
            content=b'{"type":"event_callback"}',
            headers={
                "X-Slack-Request-Timestamp": str(int(time.time())),
                "X-Slack-Signature": "v0=invalid",
                "Content-Type": "application/json",
            },
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_digest_generate_requires_auth(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/digest/generate")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_digest_generate_with_auth(app):
    with patch("app.main.generate_digest"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/digest/generate",
                headers={"Authorization": "Bearer test-secret"},
            )
    assert response.status_code == 200


def _sign(body: str, timestamp: str) -> str:
    sig_basestring = f"v0:{timestamp}:{body}".encode()
    return "v0=" + hmac.new(
        b"test-signing-secret", sig_basestring, hashlib.sha256
    ).hexdigest()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_main.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 4: Implement `app/main.py`**

```python
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import BackgroundTasks, FastAPI, Request, Response

from app.config import Settings
from app.digest_generator import generate_digest
from app.gemini_client import GeminiClient
from app.sheets_client import SheetsClient
from app.slack_client import SlackClient
from app.slack_handler import process_message, verify_slack_signature

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = Settings()

    slack_client = SlackClient(settings.slack_bot_token)
    sheets_client = SheetsClient(
        settings.google_sheets_credentials_file, settings.spreadsheet_id
    )
    gemini_client = GeminiClient(settings.gemini_api_key)

    scheduler = AsyncIOScheduler()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        scheduler.add_job(
            _run_digest,
            "cron",
            day_of_week=settings.digest_cron_day,
            hour=settings.digest_cron_hour,
            minute=settings.digest_cron_minute,
        )
        scheduler.start()
        logger.info("Scheduler started: digest at %s %02d:%02d",
                     settings.digest_cron_day, settings.digest_cron_hour, settings.digest_cron_minute)
        yield
        scheduler.shutdown()

    app = FastAPI(lifespan=lifespan)

    def _run_digest():
        generate_digest(sheets_client, gemini_client, slack_client, settings.digest_channel_id)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/slack/events")
    async def slack_events(request: Request, background_tasks: BackgroundTasks):
        body = await request.body()
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")

        if not verify_slack_signature(settings.slack_signing_secret, body, timestamp, signature):
            return Response(status_code=403)

        payload = await request.json()

        if payload.get("type") == "url_verification":
            return {"challenge": payload["challenge"]}

        event = payload.get("event", {})
        if event.get("type") == "message" and "subtype" not in event:
            background_tasks.add_task(
                process_message, event, slack_client, sheets_client, settings.digest_channel_id
            )

        return Response(status_code=200)

    @app.post("/digest/generate")
    async def manual_digest(request: Request, background_tasks: BackgroundTasks):
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {settings.admin_secret}":
            return Response(status_code=401)

        background_tasks.add_task(_run_digest)
        return {"status": "digest generation started"}

    return app


app = create_app()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_main.py -v`
Expected: 5 passed

- [ ] **Step 6: Run all tests**

Run: `pytest -v`
Expected: All tests pass (22 total)

- [ ] **Step 7: Commit**

```bash
git add app/main.py tests/test_main.py requirements.txt
git commit -m "feat: FastAPI app with Slack events, digest generation, and scheduler"
```

---

### Task 8: Docker and Deployment Config

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.gitignore`

- [ ] **Step 1: Create `Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create `docker-compose.yml`**

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./credentials.json:/app/credentials.json:ro
    restart: unless-stopped
```

- [ ] **Step 3: Create `.gitignore`**

```
__pycache__/
*.pyc
.env
credentials.json
.pytest_cache/
*.egg-info/
dist/
build/
```

- [ ] **Step 4: Commit**

```bash
git add Dockerfile docker-compose.yml .gitignore
git commit -m "feat: Docker and deployment configuration"
```

---

### Task 9: Nginx Config and Deploy Instructions

**Files:**
- Create: `deploy/nginx.conf`

- [ ] **Step 1: Create `deploy/nginx.conf`**

```nginx
server {
    listen 443 ssl;
    server_name copilot4.run;

    ssl_certificate /etc/letsencrypt/live/copilot4.run/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/copilot4.run/privkey.pem;

    location /slack/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /digest/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add deploy/
git commit -m "feat: nginx config for reverse proxy"
```

- [ ] **Step 3: Final — run all tests one more time**

Run: `pytest -v`
Expected: All 22 tests pass.

- [ ] **Step 4: Final commit with all files verified**

```bash
git log --oneline
```

Verify all 9 commits are present.
