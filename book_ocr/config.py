import os
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
_dotenv_path = _project_root / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(_dotenv_path)
except ImportError:
    pass


class Settings:
    GEMINI_API_KEY: str
    GOOGLE_CREDS_PATH: str
    SPREADSHEET_ID: str
    DRIVE_FOLDER_ID: str

    def __init__(self) -> None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            try:
                import streamlit as st
                key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                pass
        if not key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Set it via: export GEMINI_API_KEY='your-key'"
            )
        self.GEMINI_API_KEY = key

        creds = os.getenv("GOOGLE_CREDS_PATH", "cred.json")
        creds_json = os.getenv("GOOGLE_CREDENTIALS")
        resolved = Path(creds)
        if not resolved.exists() and not creds_json:
            raise FileNotFoundError(
                f"Google service account file not found at: {resolved.resolve()}. "
                "Set GOOGLE_CREDS_PATH env var or place cred.json in the project root."
            )
        self.GOOGLE_CREDS_PATH = str(resolved.resolve())

        self.SPREADSHEET_ID = os.getenv(
            "SPREADSHEET_ID",
            "1ZkNa2vhiRXRVKmcolnFzpgzTfI6vkJmY-nE7KdXudCE",
        )
        self.DRIVE_FOLDER_ID = os.getenv(
            "DRIVE_FOLDER_ID",
            "12TadHeCcv2jvFnkmJxotsTghGFU5rSWV",
        )


settings = Settings()
