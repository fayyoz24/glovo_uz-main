from django.utils.text import slugify
from django.db import transaction
from apps.merchants.models import Merchant
from apps.merchants.constants import MerchantStatus


def _unique_slug(name: str) -> str:
    base = slugify(name)
    slug = base
    counter = 1
    while Merchant.objects.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def create_merchant(owner, validated_data: dict) -> Merchant:
    with transaction.atomic():
        name = validated_data.pop("name")
        validated_data.setdefault("slug", _unique_slug(name))
        validated_data.setdefault("status", MerchantStatus.PENDING)
        merchant = Merchant.objects.create(name=name, owner=owner, **validated_data)
    return merchant


def update_merchant(merchant: Merchant, validated_data: dict) -> Merchant:
    for field, value in validated_data.items():
        setattr(merchant, field, value)
    merchant.save()
    return merchant
