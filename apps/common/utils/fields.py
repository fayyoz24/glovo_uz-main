from rest_framework import serializers

from apps.common.utils.image import compress_image_to_limit


class CompressedImageField(serializers.ImageField):
    """
    Oddiy DRF ImageField bilan bir xil ishlaydi, faqat `max_bytes` dan katta
    yuklangan rasmlarni xato qaytarish o'rniga avtomatik siqib (sifat/o'lcham
    pasaytirib) qabul qiladi. Frontendda foydalanuvchiga "rasm hajmi katta"
    degan xato ko'rsatish shart emas — server o'zi moslashtiradi.
    """

    def __init__(self, *args, max_bytes: int = 200 * 1024, **kwargs):
        self.max_bytes = max_bytes
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        file = super().to_internal_value(data)
        if file.size > self.max_bytes:
            file = compress_image_to_limit(file, max_bytes=self.max_bytes)
        return file