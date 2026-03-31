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
