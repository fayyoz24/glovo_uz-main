import os
import uuid


def product_image_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{ext}"

    return f"catalog/product_images/{instance.name_uz}/{filename}"