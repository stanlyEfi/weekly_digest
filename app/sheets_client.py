import logging

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "Messages"
COLUMNS = ["user_id", "text", "timestamp", "week_number", "processed", "ts", "channel", "username", "role"]


class SheetsClient:
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        self.service = build("sheets", "v4", credentials=creds)
        self.spreadsheet_id = spreadsheet_id

    def append_row(self, row: dict) -> None:
        values = [[row.get(col, "") for col in COLUMNS]]
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{SHEET_NAME}!A:I",
            valueInputOption="USER_ENTERED",
            body={"values": values},
        ).execute()

    def get_all_rows(self) -> list[dict]:
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=f"{SHEET_NAME}!A:I")
            .execute()
        )
        values = result.get("values", [])
        if len(values) < 2:
            return []
        headers = values[0]
        return [dict(zip(headers, row)) for row in values[1:]]
