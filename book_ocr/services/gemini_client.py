from pathlib import Path

from PIL import Image
from google import genai
from google.genai import types

from book_ocr.models import BookData

EXTRACTION_PROMPT = (
    "استخرج البيانات من صورة الغلاف وضعها في JSON بنفس الحقول. "
    "ضع 0 إذا لم توجد القيمة."
)

AVAILABLE_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.5-pro-exp-03-25",
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-3.5-flash",
]


def extract_book_data(image_path: str, model_name: str = "gemini-2.0-flash") -> BookData:
    resolved = Path(image_path)
    if not resolved.exists():
        raise FileNotFoundError(f"Image not found: {resolved.resolve()}")

    from book_ocr.config import settings

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    img = Image.open(str(resolved))

    response = client.models.generate_content(
        model=model_name,
        contents=[img, EXTRACTION_PROMPT],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BookData,
            temperature=0.1,
        ),
    )

    if response.parsed is None:
        raise ValueError(
            "Gemini returned empty response. "
            f"Full response: {response.text}"
        )

    return response.parsed
