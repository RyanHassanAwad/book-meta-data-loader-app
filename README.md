# 📚 Book Cover OCR → Google Sheets & Drive

استخراج بيانات الكتب من صور الأغلفة باستخدام Gemini AI، مع حفظ تلقائي في Google Sheets ورفع الصور إلى Google Drive.

## 🚀 Quick Start

### 1. الإعدادات المطلوبة

```bash
# مفتاح Gemini API (إجباري)
export GEMINI_API_KEY="AIzaSy..."

# مسار ملف credentials (اختياري، الافتراضي: cred.json)
export GOOGLE_CREDS_PATH="cred.json"

# معرف Google Sheet (اختياري)
export SPREADSHEET_ID="1ZkNa2vhiRXRVKmcolnFzpgzTfI6vkJmY-nE7KdXudCE"

# معرف مجلد Google Drive (اختياري)
export DRIVE_FOLDER_ID="12TadHeCcv2jvFnkmJxotsTghGFU5rSWV"
```

### 2. تشغيل التطبيق

```bash
# تنشيط البيئة الافتراضية
source .venv/bin/activate

# واجهة الأوامر (CLI)
python -m book_ocr.main

# واجهة الويب (Streamlit)
streamlit run streamlit_app/app.py
```

## 🧭 واجهة Streamlit

| الخطوة | الوصف |
|--------|-------|
| **١. رفع الصورة** | رفع صورة غلاف الكتاب (أو صورتين للدمج) |
| **٢. استخراج البيانات** | استخراج البيانات عبر Gemini Vision API |
| **٣. مراجعة وتعديل** | تعديل الحقول المستخرجة قبل الحفظ |
| **٤. حفظ ومزامنة** | حفظ في Google Sheets + رفع الصورة إلى Drive |

## 📁 هيكل المشروع

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

streamlit_app/           # Web UI
├── app.py               # Streamlit application
└── requirements.txt
```

## ✅ Zero-Regression

الكود الأساسي (`book_ocr/`) لم يتغير — نفس المنطق يعمل بالضبط عبر CLI و Streamlit.

## 🛠 التطوير

```bash
# تشغيل الفاحص
ruff check book_ocr/ streamlit_app/

# تشغيل Streamlit محلياً
streamlit run streamlit_app/app.py
```
```

