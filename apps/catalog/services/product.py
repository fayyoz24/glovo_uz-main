from django.db import transaction
from apps.catalog.constants import ProductStatus
from apps.catalog.models import Product
from apps.catalog.exceptions import ProductNotFound
import os
import uuid


def create_product(merchant, validated_data: dict) -> Product:
    with transaction.atomic():
        product = Product.objects.create(merchant=merchant, **validated_data)
    return product


def update_product(product_id, merchant, validated_data: dict) -> Product:
    product = Product.objects.filter(id=product_id, merchant=merchant).first()
    if not product:
        raise ProductNotFound()

    was_out_of_stock = product.status == ProductStatus.OUT_OF_STOCK
    for field, value in validated_data.items():
        setattr(product, field, value)

    # Do'kon egasi ombordagi sonni qayta to'ldirsa (0 dan yuqoriga), va bu status
    # avtomatik "tugagan"ga o'tgan bo'lsa — mahsulotni qayta faollashtiramiz.
    if (
        was_out_of_stock
        and "stock_qty" in validated_data
        and product.stock_qty > 0
        and "status" not in validated_data
    ):
        product.status = ProductStatus.ACTIVE
        if "is_available" not in validated_data:
            product.is_available = True

    product.save()
    return product


def toggle_product_availability(product_id, merchant, is_available: bool) -> Product:
    product = Product.objects.filter(id=product_id, merchant=merchant).first()
    if not product:
        raise ProductNotFound()
    product.is_available = is_available
    product.save(update_fields=["is_available", "updated_at"])
    return product


