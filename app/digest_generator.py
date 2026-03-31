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
