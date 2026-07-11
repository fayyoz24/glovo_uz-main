import os
import uuid


def _merchant_upload_path(subfolder, instance, filename):
    """
    Do'kon rasmlari uchun umumiy yo'l generatori.

    `instance.name` (yoki boshqa o'zgaruvchan maydon) emas, `instance.id`
    ishlatiladi — chunki:
      - do'kon nomi bo'sh joy/kirill/maxsus belgilar bo'lishi mumkin va
        fayl tizimi yoki S3 kabi storage'da muammo tug'dirishi mumkin;
      - nom keyinchalik o'zgarishi mumkin, id esa doim barqaror.
    """
    ext = os.path.splitext(filename)[1].lower()
    new_filename = f"{uuid.uuid4()}{ext}"
    return f"merchants/{subfolder}/{instance.id}/{new_filename}"


def merchant_logo_upload_path(instance, filename):
    return _merchant_upload_path("merchant_logos", instance, filename)


def merchant_cover_upload_path(instance, filename):
    return _merchant_upload_path("merchant_covers", instance, filename)