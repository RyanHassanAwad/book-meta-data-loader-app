from pydantic import BaseModel, Field
from typing import Union


class BookData(BaseModel):
    العنوان: str = Field(description="اسم الكتاب الرئيسي")
    المؤلف: Union[str, int] = Field(description="اسم المؤلف أو 0")
    المحقق: Union[str, int] = Field(description="اسم المحقق أو 0")

    التصنيف_الرئيسي: str = Field(
        alias="التصنيف الرئيسي",
        description="التصنيف العام (مثل: حديث، فقه، لغة)",
    )
    التصنيف_الفرعي: Union[str, int] = Field(
        alias="التصنيف الفرعي",
        description="التصنيف الدقيق أو 0",
    )
    دار_الطباعة: Union[str, int] = Field(
        alias="دار الطباعة",
        description="دار النشر أو 0",
    )
    سنة_الطباعة_الهجرية: Union[str, int] = Field(
        alias="سنة الطباعة الهجرية",
        description="السنة الهجرية أو 0",
    )
    سنة_الطباعة_الميلادية: Union[str, int] = Field(
        alias="سنة الطباعة الميلادية",
        description="السنة الميلادية أو 0",
    )
    رقم_الطبعة: Union[str, int] = Field(
        alias="رقم الطبعة",
        description="رقم الطبعة أو 0",
    )
    عدد_الأجزاء: Union[str, int] = Field(
        alias="عدد الأجزاء",
        description="عدد الأجزاء أو 0",
    )
    نوع_الكتاب: str = Field(
        alias="نوع الكتاب",
        description="نوع الكتاب المستنتج (تفسير، عقيدة...)",
    )
    رقم_الجزء: Union[str, int] = Field(
        alias="رقم الجزء",
        description="رقم الجزء المستخرج من الغلاف أو 0",
    )
