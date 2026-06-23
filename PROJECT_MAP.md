# PROJECT MAP: Book Cover OCR → Google Sheets/Drive

## Vision
Automated extraction of Arabic book metadata from cover images using Gemini Vision AI, with direct pipeline to Google Sheets and Drive.

## Architecture (Clean Architecture Layers)

```
book_ocr/                # Core logic (CLI)
├── config.py            # Settings (env vars)
├── models.py            # BookData (Pydantic)
├── main.py              # CLI entry point
├── services/
│   ├── gemini_client.py # Gemini Vision API
│   ├── sheets_client.py # Google Sheets
│   └── drive_client.py  # Google Drive
├── utils/
│   └── image_utils.py   # Image merge
└── requirements.txt

streamlit_app/           # Web UI layer
├── app.py               # Streamlit application
└── requirements.txt
```

## Module Status

| Module | Status | Layer | Acceptance Criteria |
|--------|--------|-------|-------------------|
| config.py | ✅ DONE | core | Reads env vars with fallback defaults; validates at init |
| models.py | ✅ DONE | core | BookData validates 12 fields with aliases |
| gemini_client.py | ✅ DONE | core | Returns parsed BookData; raises on API/model failure |
| sheets_client.py | ✅ DONE | core | Appends row to configured sheet |
| drive_client.py | ✅ DONE | core | Uploads image to Drive; returns file ID |
| image_utils.py | ✅ DONE | core | Merges 2 images side-by-side |
| main.py | ✅ DONE | core | CLI workflow: extract → review → confirm → sheets+drive |
| app.py | ✅ DONE | streamlit | Web UI: upload → extract → review → save, with logging |
| requirements.txt | ✅ DONE | both | Pins all dependencies |

## Key Decisions
- API key from env var `GEMINI_API_KEY` only; never hardcoded.
- Service account credentials path from env var `GOOGLE_CREDS_PATH` (default `cred.json`).
- Sheet/Drive IDs from env vars with fallback to current hardcoded values.
