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
