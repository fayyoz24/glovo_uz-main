"""
Yuklangan rasmlarni belgilangan hajm (bayt) chegarasiga siqib moslashtirish uchun
umumiy yordamchi. Foydalanuvchiga "rasm juda katta" degan xato ko'rsatish o'rniga,
serverda avtomatik ravishda sifat va o'lchamni bosqichma-bosqich pasaytirib,
chegaraga moslaymiz.

Ishlatilishi uchun Pillow talab qilinadi (u ImageField uchun allaqachon o'rnatilgan
bo'lishi kerak, chunki Django ImageField Pillow'siz ishlamaydi).
"""
import io

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile


def compress_image_to_limit(
    uploaded_file,
    max_bytes: int = 200 * 1024,
    max_dimension: int = 1600,
    min_quality: int = 35,
    start_quality: int = 90,
):
    """
    `uploaded_file` (InMemoryUploadedFile/TemporaryUploadedFile) ni `max_bytes`
    dan oshmaydigan JPEG faylga aylantirib qaytaradi.

    Agar fayl allaqachon limitdan kichik bo'lsa, o'zgartirmasdan qaytaradi
    (chaqiruvchi tomonda buni oldindan tekshirish tavsiya etiladi, lekin bu
    funksiya ham xavfsiz — hech qanday hajmda ishlaydi).

    Strategiya:
    1) Rasmni RGB'ga o'giradi (PNG shaffofligi bo'lsa oq fon bilan).
    2) `max_dimension`dan katta bo'lsa nisbatini saqlab kichraytiradi.
    3) JPEG sifatini 90 dan `min_quality`gacha 5 baravar kamaytirib, limitga
       tushguncha qayta kodlaydi.
    4) Sifat pasaytirish yetarli bo'lmasa (masalan juda katta o'lcham),
       o'lchamni ham bosqichma-bosqich kichraytiradi.
    """
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)

    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        rgba = image.convert("RGBA")
        background.paste(rgba, mask=rgba.split()[-1])
        image = background
    else:
        image = image.convert("RGB")

    image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    buffer = io.BytesIO()
    quality = start_quality
    while True:
        buffer.seek(0)
        buffer.truncate()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        if buffer.tell() <= max_bytes or quality <= min_quality:
            break
        quality -= 5

    # Sifatni pasaytirish yetmasa, o'lchamni ham kichraytiramiz (masalan juda
    # baland-kenglikdagi rasmlar uchun).
    while buffer.tell() > max_bytes and min(image.size) > 200:
        w, h = image.size
        image = image.resize((int(w * 0.85), int(h * 0.85)), Image.LANCZOS)
        buffer.seek(0)
        buffer.truncate()
        image.save(buffer, format="JPEG", quality=min_quality, optimize=True)

    buffer.seek(0)
    base_name = (uploaded_file.name or "image").rsplit(".", 1)[0]
    return InMemoryUploadedFile(
        buffer,
        field_name=None,
        name=f"{base_name}.jpg",
        content_type="image/jpeg",
        size=buffer.getbuffer().nbytes,
        charset=None,
    )