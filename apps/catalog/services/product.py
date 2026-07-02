from django.db import transaction
from apps.catalog.models import Product
from apps.catalog.exceptions import ProductNotFound


def create_product(merchant, validated_data: dict) -> Product:
    with transaction.atomic():
        product = Product.objects.create(merchant=merchant, **validated_data)
    return product


def update_product(product_id, merchant, validated_data: dict) -> Product:
    product = Product.objects.filter(id=product_id, merchant=merchant).first()
    if not product:
        raise ProductNotFound()
    for field, value in validated_data.items():
        setattr(product, field, value)
    product.save()
    return product


def toggle_product_availability(product_id, merchant, is_available: bool) -> Product:
    product = Product.objects.filter(id=product_id, merchant=merchant).first()
    if not product:
        raise ProductNotFound()
    product.is_available = is_available
    product.save(update_fields=["is_available", "updated_at"])
    return product
