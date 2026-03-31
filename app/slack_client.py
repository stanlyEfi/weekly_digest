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
