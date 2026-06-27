import json
import os

import gspread
from google.oauth2.service_account import Credentials

from book_ocr.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_credentials() -> Credentials:
    raw = os.getenv("GOOGLE_CREDENTIALS")
    if raw:
        info = json.loads(raw)
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    return Credentials.from_service_account_file(
        settings.GOOGLE_CREDS_PATH, scopes=SCOPES
    )


def _get_worksheet():
    creds = _get_credentials()
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(settings.SPREADSHEET_ID)
    return spreadsheet.get_worksheet(0)


def append_row(values: list) -> None:
    worksheet = _get_worksheet()
    worksheet.append_row(values)
