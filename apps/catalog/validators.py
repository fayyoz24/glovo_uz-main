from django.conf import settings
from django.core.exceptions import ValidationError

DEFAULT_PRODUCT_IMAGE_MAX_SIZE_KB = 200


def validate_product_image_size(file):
    """
    Mahsulot rasmi hajmini tekshiradi.
    Default limit 200 KB (settings.PRODUCT_IMAGE_MAX_SIZE_KB orqali o'zgartirish mumkin).
    """
    max_kb = getattr(settings, "PRODUCT_IMAGE_MAX_SIZE_KB", DEFAULT_PRODUCT_IMAGE_MAX_SIZE_KB)
    max_bytes = max_kb * 1024
    if file.size > max_bytes:
        raise ValidationError(
            f"Rasm hajmi {max_kb} KB dan oshmasligi kerak. "
            f"Yuklangan fayl hajmi: {file.size / 1024:.0f} KB."
        )
