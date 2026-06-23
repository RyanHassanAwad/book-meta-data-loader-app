import os
import sys

from book_ocr.models import BookData
from book_ocr.services.gemini_client import extract_book_data
from book_ocr.services.sheets_client import append_row
from book_ocr.services.drive_client import upload_image

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


def _review(record: dict[str, object]) -> dict[str, object]:
    print("\nالبيانات المستخرجة - اضغط Enter للإبقاء على القيمة أو أدخل قيمة جديدة:")
    for label in FIELD_LABELS:
        current = record[label]
        user_input = input(f"  {label} [{current}]: ").strip()
        if user_input:
            record[label] = user_input
    return record


def _confirm_save() -> bool:
    answer = input(
        "\nهل تريد الحفظ في Google Sheets؟ (y/n) [default: yes]: "
    ).strip().lower()
    return answer != "n"


def run(image_path: str) -> None:
    if not os.path.exists(image_path):
        print(f"خطأ: الملف غير موجود: {image_path}")
        sys.exit(1)

    print(f"[*] جاري تحليل غلاف الكتاب {os.path.basename(image_path)}...")

    try:
        data = extract_book_data(image_path)
    except Exception as e:
        print(f"فشل استخراج البيانات من Gemini: {e}")
        sys.exit(1)

    record = _to_dict(data)
    record = _review(record)

    if not _confirm_save():
        print("تم الإلغاء.")
        return

    try:
        try:
            file_id = upload_image(image_path)
            link = f"https://drive.google.com/file/d/{file_id}/view"
            record["رابط الصورة"] = link
            print("✅ تم رفع الصورة إلى Drive")
        except Exception as e:
            print(f"⚠️ لم نتمكن من رفع الصورة إلى Drive: {e}")
            print("💡 استخدم Shared Drive بدلاً من My Drive.")
            record["رابط الصورة"] = "فشل الرفع"

        append_row(list(record.values()))
        print("✅ تم حفظ البيانات في Google Sheets!")
    except Exception as e:
        print(f"حدث خطأ أثناء الحفظ: {e}")
        sys.exit(1)


def main() -> None:
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = input("أدخل مسار الصورة: ").strip()

    run(image_path)


if __name__ == "__main__":
    main()
