import os
from pathlib import Path


class Settings:
    GEMINI_API_KEY: str
    GOOGLE_CREDS_PATH: str
    SPREADSHEET_ID: str
    DRIVE_FOLDER_ID: str

    def __init__(self) -> None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            key = "AIzaSyC79ggE_okBO22iRsJIb3-DkCUKuPzXmdo"
        self.GEMINI_API_KEY = key

        creds = os.getenv("GOOGLE_CREDS_PATH", "cred.json")
        resolved = Path(creds)
        if not resolved.exists():
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
