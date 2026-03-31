from unittest.mock import MagicMock, patch

from app.gemini_client import GeminiClient


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
