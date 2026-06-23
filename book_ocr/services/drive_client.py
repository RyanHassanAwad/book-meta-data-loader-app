import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from book_ocr.config import settings

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_CREDS_PATH, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials)


def upload_image(image_path: str) -> str:
    service = _get_drive_service()

    file_metadata = {
        "name": os.path.basename(image_path),
        "parents": [settings.DRIVE_FOLDER_ID],
    }

    media = MediaFileUpload(image_path, resumable=True)

    file = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True,
        )
        .execute()
    )

    return file.get("id")
