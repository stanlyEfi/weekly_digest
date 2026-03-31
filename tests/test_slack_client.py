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
