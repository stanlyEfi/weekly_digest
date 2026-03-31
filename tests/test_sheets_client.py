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
            ["user_id", "text", "timestamp", "week_number", "processed", "ts", "channel", "username", "role"],
            ["U123", "Launched feature X", "2026-03-31T10:00:00", "14", "", "123.456", "C-ch", "Stan", "PM"],
            ["U456", "Revenue grew 20%", "2026-03-30T09:00:00", "14", "", "789.012", "C-ch", "Kirill", "CEO"],
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
