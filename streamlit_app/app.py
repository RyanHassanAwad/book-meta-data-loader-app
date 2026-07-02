import base64
import json as _json
import logging
import sys
import tempfile
import textwrap
from pathlib import Path

import streamlit as st

# ── Page config must be the very first Streamlit command ──
st.set_page_config(
    page_title="استخراج بيانات الكتب",
    page_icon="📚",
    layout="wide",
)

# ── Custom styling ──
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    * { font-family: 'Cairo', sans-serif !important; }
    .stApp { background-color: #F8F5F0; }
    .st-emotion-cache-1v0mbdj, .st-emotion-cache-1104ytp {
        background-color: #F8F5F0;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Cairo', sans-serif !important;
        color: #3E2723 !important;
    }
    .stButton button {
        background-color: #2E7D32;
        color: white;
        border-radius: 8px;
        font-family: 'Cairo', sans-serif;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1.5rem;
    }
    .stButton button:hover {
        background-color: #1B5E20;
        color: white;
    }
    .stTextInput input, .stTextInput label {
        font-family: 'Cairo', sans-serif !important;
    }
    input, textarea, [contenteditable] { direction: auto; }
    .st-expander {
        border: 1px solid #D7CCC8;
        border-radius: 10px;
        background-color: #FFFFFF;
    }
    .stAlert {
        font-family: 'Cairo', sans-serif !important;
    }
    .st-emotion-cache-1yjvs5a {
        color: #3E2723;
    }
    span[dir="rtl"] { direction: rtl; display: inline; }
    span[dir="ltr"] { direction: ltr; display: inline; }
</style>
""", unsafe_allow_html=True)

# ── Write credentials from secrets if missing on cloud ──
_cred_path = Path(__file__).resolve().parent.parent / "cred.json"
if not _cred_path.exists():
    _b64 = st.secrets.get("GOOGLE_CREDENTIALS_B64")
    if _b64:
        _cred_path.write_text(base64.b64decode(_b64).decode("utf-8"))
        st.success("✅ تم تحميل ملف الاعتماد من الأسرار")
    else:
        _raw = st.secrets.get("GOOGLE_CREDENTIALS")
        if _raw:
            try:
                _data = _json.loads(_raw)
            except _json.JSONDecodeError:
                _data = _json.loads(_raw, strict=False)

            _pk = _data.get("private_key", "")
            if _pk:
                _lines = _pk.replace("\r", "").split("\n")
                _b64_lines = [
                    l for l in _lines
                    if l and not l.startswith("-----")
                ]
                _clean = "".join(_b64_lines)
                if _clean:
                    _wrapped = "\n".join(textwrap.wrap(_clean, width=64))
                    _data["private_key"] = (
                        "-----BEGIN PRIVATE KEY-----\n"
                        f"{_wrapped}\n"
                        "-----END PRIVATE KEY-----\n"
                    )

            _cred_path.write_text(_json.dumps(_data, indent=2))
            st.success("✅ تم تحميل ملف الاعتماد من الأسرار")

# ── Attempt to load core library ──
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from book_ocr.services.gemini_client import extract_book_data
    from book_ocr.services.sheets_client import append_row
    from book_ocr.services.drive_client import upload_image
    from book_ocr.utils.image_utils import merge_side_by_side, transform_image
    from book_ocr.models import BookData

    CORE_LOADED = True
except Exception as exc:
    CORE_LOADED = False
    CORE_ERROR = str(exc)

# ── Logging setup ──
logger = logging.getLogger("book_ocr_streamlit")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# ── Session state initialisation ──
DEFAULT_STATE = {
    "image_path": None,
    "extracted_data": None,
    "book_record": None,
    "logs": [],
    "step": "upload",
    "merged_image_path": None,
    "upload_key": 0,
    "manual_key": 0,
    "selected_model": "gemini-2.0-flash",
    # image transforms
    "img1_original_path": None,
    "img1_current_path": None,
    "img1_rotation": 0,
    "img1_flip_h": False,
    "img1_flip_v": False,
    "img2_original_path": None,
    "img2_current_path": None,
    "img2_rotation": 0,
    "img2_flip_h": False,
    "img2_flip_v": False,
}

for k, v in DEFAULT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helper functions ──
FIELD_LABELS = [
    "العنوان",
    "المؤلف",
    "المحقق",
    "التصنيف الرئيسي",
    "التصنيف الفرعي",
    "دار الطباعة",
    "سنة الطباعة الهجرية",
    "سنة الطباعة الميلادية",
    "رقم الطبعة",
    "عدد الأجزاء",
    "نوع الكتاب",
    "رقم الجزء",
    "رابط الصورة",
]


def _save_uploaded(uploaded_file) -> str | None:
    if uploaded_file is None:
        return None
    suffix = Path(uploaded_file.name).suffix or ".jpg"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.getbuffer())
    path = tmp.name
    tmp.close()
    logger.info("Saved uploaded file to %s", path)
    st.session_state.logs.append(f"Saved uploaded file → {path}")
    return path


def _to_dict(data: BookData) -> dict[str, object]:
    return {
        "العنوان": data.العنوان,
        "المؤلف": data.المؤلف,
        "المحقق": data.المحقق,
        "التصنيف الرئيسي": data.التصنيف_الرئيسي,
        "التصنيف الفرعي": data.التصنيف_الفرعي,
        "دار الطباعة": data.دار_الطباعة,
        "سنة الطباعة الهجرية": data.سنة_الطباعة_الهجرية,
        "سنة الطباعة الميلادية": data.سنة_الطباعة_الميلادية,
        "رقم الطبعة": data.رقم_الطبعة,
        "عدد الأجزاء": data.عدد_الأجزاء,
        "نوع الكتاب": data.نوع_الكتاب,
        "رقم الجزء": data.رقم_الجزء,
        "رابط الصورة": "",
    }


def _reset():
    upload_key = st.session_state.get("upload_key", 0) + 1
    for k in DEFAULT_STATE:
        st.session_state[k] = DEFAULT_STATE[k]
    st.session_state.upload_key = upload_key
    st.rerun()


def _apply_transforms(img_key: str):
    original_path = st.session_state.get(f"{img_key}_original_path")
    if not original_path:
        return None
    rotation = st.session_state.get(f"{img_key}_rotation", 0)
    flip_h = st.session_state.get(f"{img_key}_flip_h", False)
    flip_v = st.session_state.get(f"{img_key}_flip_v", False)
    if rotation == 0 and not flip_h and not flip_v:
        result = original_path
    else:
        result = transform_image(
            original_path,
            rotation=rotation,
            flip_h=flip_h,
            flip_v=flip_v,
        )
    st.session_state[f"{img_key}_current_path"] = result
    return result


# ── Sidebar ──
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/book.png", width=64)
    st.markdown('<span dir="rtl">### 📚 استخراج بيانات الكتب</span>', unsafe_allow_html=True)
    st.divider()

    if not CORE_LOADED:
        st.error(f"⚠️ فشل تحميل المكتبات الأساسية:\n\n{CORE_ERROR}")
        st.stop()

    CONFIG_OK = False

    try:
        from book_ocr.config import settings
        from book_ocr.services.gemini_client import AVAILABLE_MODELS

        _current_model = st.session_state.get("selected_model", "gemini-2.0-flash")
        _default_idx = AVAILABLE_MODELS.index(_current_model) if _current_model in AVAILABLE_MODELS else 0
        _model_choice = st.selectbox("🤖 اختر النموذج", AVAILABLE_MODELS, index=_default_idx, key="model_selector")
        st.session_state.selected_model = _model_choice
        st.caption(f"النموذج الحالي: `{_model_choice}`")

        has_key = bool(settings.GEMINI_API_KEY)
        has_creds = Path(settings.GOOGLE_CREDS_PATH).expanduser().exists()
        has_sheet = bool(settings.SPREADSHEET_ID)
        has_folder = bool(settings.DRIVE_FOLDER_ID)
        CONFIG_OK = has_key and has_creds and has_sheet
    except Exception:
        pass

    st.divider()

    if st.button("📤 رفع كتاب آخر", use_container_width=True, type="primary"):
        _reset()

    st.divider()

    _sid = settings.SPREADSHEET_ID
    _fid = settings.DRIVE_FOLDER_ID

    if _sid:
        st.link_button(
            "📊 فتح Google Sheet",
            f"https://docs.google.com/spreadsheets/d/{_sid}",
            use_container_width=True,
        )

    if _fid:
        st.link_button(
            "📁 فتح Google Drive",
            f"https://drive.google.com/drive/folders/{_fid}",
            use_container_width=True,
        )

# ── Main UI ──
st.title("📖 استخراج بيانات الكتب من صور الأغلفة")
st.markdown("---")

# ═══════════════════════════════════════════════
# Manual entry (no model / no image)
# ═══════════════════════════════════════════════
with st.expander(" يدوي"):
    st.markdown('<span dir="rtl">أدخل بيانات الكتاب يدويًا واحفظها مباشرة في Google Sheets</span>', unsafe_allow_html=True)
    _m_cols = st.columns(2)
    _manual = {}
    for i, _label in enumerate(FIELD_LABELS):
        _col = _m_cols[i % 2]
        _col.markdown(f'<p dir="auto" style="margin-bottom:2px">{_label}</p>', unsafe_allow_html=True)
        _manual[_label] = _col.text_input("", key=f"manual_{st.session_state.manual_key}_{_label}")

    _b_cols = st.columns(2)
    with _b_cols[0]:
        if st.button("💾 حفظ في Sheets", type="primary", use_container_width=True, key="save_manual"):
            if not CONFIG_OK:
                st.error("⚠️ الإعدادات غير مكتملة. تحقق من الإعدادات.")
            else:
                with st.spinner("جاري الحفظ في Google Sheets..."):
                    try:
                        append_row(list(_manual.values()))
                        st.success("✅ تم الحفظ في Google Sheets!")
                        st.session_state.logs.append("✅ إضافة يدوية: تم الحفظ")
                    except Exception as e:
                        st.error(f"خطأ في الحفظ: {e}")
                        st.session_state.logs.append(f"❌ فشل الحفظ اليدوي: {e}")
    with _b_cols[1]:
        if st.button("📝 إضافة كتاب آخر", use_container_width=True):
            st.session_state.manual_key += 1
            st.rerun()

st.markdown("---")

# ═══════════════════════════════════════════════
# STEP 1 — Upload & Transform
# ═══════════════════════════════════════════════
st.header("الخطوة ١: رفع الصورة وتحويلها")
with st.container(border=True):
    col1, col2 = st.columns(2)

    with col1:
        img1_file = st.file_uploader(
            "الصورة الأولى (يمين)",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"img1_{st.session_state.upload_key}",
        )
        if img1_file:
            _prev1 = f"img1_prev_name_{st.session_state.upload_key}"
            if st.session_state.get(_prev1) != img1_file.name:
                path = _save_uploaded(img1_file)
                st.session_state.img1_original_path = path
                st.session_state.img1_rotation = 0
                st.session_state.img1_flip_h = False
                st.session_state.img1_flip_v = False
                st.session_state.img1_current_path = path
                st.session_state[_prev1] = img1_file.name

            _disp1 = st.session_state.img1_current_path
            if _disp1 and Path(_disp1).exists():
                st.image(_disp1, caption="الصورة الأولى", use_container_width=True)
            else:
                st.image(img1_file, caption="الصورة الأولى", use_container_width=True)

            _b1 = st.columns(4)
            with _b1[0]:
                if st.button("🔄 90°", key=f"r1_{st.session_state.upload_key}", use_container_width=True):
                    st.session_state.img1_rotation += 90
                    _apply_transforms("img1")
                    st.rerun()
            with _b1[1]:
                if st.button("🔄 90-", key=f"r2_{st.session_state.upload_key}", use_container_width=True):
                    st.session_state.img1_rotation -= 90
                    _apply_transforms("img1")
                    st.rerun()
            with _b1[2]:
                if st.button("↔", key=f"fh_{st.session_state.upload_key}", use_container_width=True):
                    st.session_state.img1_flip_h = not st.session_state.img1_flip_h
                    _apply_transforms("img1")
                    st.rerun()
            with _b1[3]:
                if st.button("↕", key=f"fv_{st.session_state.upload_key}", use_container_width=True):
                    st.session_state.img1_flip_v = not st.session_state.img1_flip_v
                    _apply_transforms("img1")
                    st.rerun()

    with col2:
        img2_file = st.file_uploader(
            "الصورة الثانية (يسار) — اختياري للدمج",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"img2_{st.session_state.upload_key}",
        )
        if img2_file:
            _prev2 = f"img2_prev_name_{st.session_state.upload_key}"
            if st.session_state.get(_prev2) != img2_file.name:
                path = _save_uploaded(img2_file)
                st.session_state.img2_original_path = path
                st.session_state.img2_rotation = 0
                st.session_state.img2_flip_h = False
                st.session_state.img2_flip_v = False
                st.session_state.img2_current_path = path
                st.session_state[_prev2] = img2_file.name

            _disp2 = st.session_state.img2_current_path
            if _disp2 and Path(_disp2).exists():
                st.image(_disp2, caption="الصورة الثانية", use_container_width=True)
            else:
                st.image(img2_file, caption="الصورة الثانية", use_container_width=True)

            _b2 = st.columns(4)
            with _b2[0]:
                if st.button("🔄 90°", key=f"r1_2_{st.session_state.upload_key}", use_container_width=True):
                    st.session_state.img2_rotation += 90
                    _apply_transforms("img2")
                    st.rerun()
            with _b2[1]:
                if st.button("🔄 90-", key=f"r2_2_{st.session_state.upload_key}", use_container_width=True):
                    st.session_state.img2_rotation -= 90
                    _apply_transforms("img2")
                    st.rerun()
            with _b2[2]:
                if st.button("↔", key=f"fh_2_{st.session_state.upload_key}", use_container_width=True):
                    st.session_state.img2_flip_h = not st.session_state.img2_flip_h
                    _apply_transforms("img2")
                    st.rerun()
            with _b2[3]:
                if st.button("↕", key=f"fv_2_{st.session_state.upload_key}", use_container_width=True):
                    st.session_state.img2_flip_v = not st.session_state.img2_flip_v
                    _apply_transforms("img2")
                    st.rerun()

    merge_clicked = st.button("🔗 دمج الصور", type="secondary")

    if merge_clicked and img1_file and img2_file:
        with st.spinner("جاري دمج الصور..."):
            p1 = st.session_state.img1_current_path
            p2 = st.session_state.img2_current_path
            merged = merge_side_by_side(p1, p2)
            st.session_state.merged_image_path = merged
            st.session_state.image_path = merged
            st.session_state.step = "extract"
            st.success(f"تم الدمج → `{merged}`")
            st.rerun()
    elif merge_clicked and not img1_file:
        st.warning("يرجى رفع الصورة الأولى على الأقل.")

    if not st.session_state.get("image_path") and img1_file and not img2_file:
        if st.button("📤 استخدام الصورة فقط (بدون دمج)", type="primary"):
            st.session_state.image_path = st.session_state.img1_current_path
            st.session_state.step = "extract"
            st.rerun()

# ═══════════════════════════════════════════════
# STEP 2 — Extract
# ═══════════════════════════════════════════════
if st.session_state.image_path:
    st.markdown("---")
    st.header("الخطوة ٢: استخراج البيانات")

    img_path = st.session_state.image_path
    st.caption(f"ملف الإدخال: `{img_path}`")

    if not CONFIG_OK:
        st.warning("⚠️ الإعدادات غير مكتملة. هذا الزر لن يعمل.")
    else:
        if st.button("🧠 استخراج باستخدام Gemini", type="primary"):
            with st.spinner("جاري تحليل غلاف الكتاب..."):
                try:
                    data = extract_book_data(img_path, model_name=st.session_state.get("selected_model", "gemini-2.0-flash"))
                    record = _to_dict(data)
                    st.session_state.extracted_data = data
                    st.session_state.book_record = record
                    st.session_state.step = "review"
                    logger.info("Extraction successful: %s", record.get("العنوان"))
                    st.session_state.logs.append(
                        f"✅ استخراج ناجح: {record.get('العنوان')}"
                    )
                    st.success("تم الاستخراج بنجاح!")
                    st.rerun()
                except Exception as e:
                    logger.error("Extraction failed: %s", e)
                    st.session_state.logs.append(f"❌ فشل الاستخراج: {e}")
                    st.error(f"فشل الاستخراج: {e}")

# ═══════════════════════════════════════════════
# STEP 3 — Review & Edit
# ═══════════════════════════════════════════════
if st.session_state.book_record:
    st.markdown("---")
    st.header("الخطوة ٣: مراجعة وتعديل البيانات")
    st.caption("عدّل القيم ثم انتقل إلى الحفظ.")

    record = st.session_state.book_record

    with st.form(key="review_form"):
        cols = st.columns(2)
        edited = {}
        for i, label in enumerate(FIELD_LABELS):
            col = cols[i % 2]
            current = str(record.get(label, ""))
            col.markdown(f'<p dir="auto" style="margin-bottom:2px">{label}</p>', unsafe_allow_html=True)
            new_val = col.text_input("", value=current, key=f"field_{label}")
            edited[label] = new_val

        submitted = st.form_submit_button("✅ تأكيد التعديلات", type="primary")

    if submitted:
        st.session_state.book_record = edited
        st.session_state.step = "save"
        st.session_state.logs.append("📝 تم تأكيد التعديلات")
        st.success("تم حفظ التعديلات! انتقل إلى الخطوة التالية.")
        st.rerun()

# ═══════════════════════════════════════════════
# STEP 4 — Save (Sheets & Drive)
# ═══════════════════════════════════════════════
if st.session_state.book_record and st.session_state.step in ("save",):
    st.markdown("---")
    st.header("الخطوة ٤: الحفظ")

    record = st.session_state.book_record
    st.json(record, expanded=False)

    col_save, col_drive = st.columns(2)

    with col_save:
        if st.button("💾 حفظ في Sheets", type="primary", use_container_width=True, key="save_sheets"):
            if not CONFIG_OK:
                st.error("⚠️ الإعدادات غير مكتملة.")
                st.stop()

            with st.spinner("جاري حفظ البيانات في Google Sheets..."):
                try:
                    append_row(list(record.values()))
                    logger.info("Sheet append successful")
                    st.session_state.logs.append("✅ تم الحفظ في Sheets")
                    st.success("✅ تم حفظ البيانات في Google Sheets!")
                except Exception as e:
                    logger.error("Sheet append failed: %s", e)
                    st.session_state.logs.append(f"❌ فشل حفظ Sheets: {e}")
                    st.error(f"خطأ في الحفظ: {e}")

    with col_drive:
        if st.button("📤 رفع الصورة إلى Drive", use_container_width=True):
            if not CONFIG_OK:
                st.error("⚠️ الإعدادات غير مكتملة.")
                st.stop()

            with st.spinner("جاري رفع الصورة إلى Drive..."):
                try:
                    file_id = upload_image(st.session_state.image_path)
                    link = f"https://drive.google.com/file/d/{file_id}/view"
                    record["رابط الصورة"] = link
                    st.session_state.logs.append(f"✅ تم الرفع إلى Drive (ID:{file_id})")
                    logger.info("Drive upload successful, ID: %s", file_id)
                    st.success(f"✅ تم رفع الصورة! [رابط]({link})")
                except Exception as e:
                    logger.error("Drive upload failed: %s", e)
                    st.session_state.logs.append(f"❌ فشل رفع Drive: {e}")
                    st.warning(
                        "⚠️ لم نتمكن من رفع الصورة إلى Drive. "
                        "قد يكون السبب: حساب الخدمة لا يدعم الرفع إلى My Drive. "
                        "حاول استخدام Shared Drive."
                    )

    st.divider()
    st.markdown('<span dir="rtl">### روابط سريعة</span>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.link_button(
            "📊 فتح Google Sheet",
            f"https://docs.google.com/spreadsheets/d/{settings.SPREADSHEET_ID}",
            use_container_width=True,
        )
    with col_b:
        st.link_button(
            "📁 فتح Google Drive",
            f"https://drive.google.com/drive/folders/{settings.DRIVE_FOLDER_ID}",
            use_container_width=True,
        )

# ═══════════════════════════════════════════════
# Activity Log
# ═══════════════════════════════════════════════
st.markdown("---")
with st.expander(" (Activity Log)", expanded=False):
    for entry in st.session_state.logs:
        st.text(entry)

    if st.button("مسح السجل"):
        st.session_state.logs = []
        st.rerun()
