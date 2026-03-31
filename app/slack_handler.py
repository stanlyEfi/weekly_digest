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
