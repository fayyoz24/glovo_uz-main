from django.utils.text import slugify
from django.db import transaction
from apps.merchants.models import Merchant, MerchantStaffProfile
from apps.merchants.constants import MerchantStatus
from apps.merchants.selectors import count_pending_merchants_for_owner
from apps.merchants.exceptions import TooManyPendingMerchants
from apps.accounts.constants import UserRole

MAX_PENDING_MERCHANTS_PER_OWNER = 3


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


def register_merchant_with_owner(user, validated_data: dict) -> Merchant:
    """
    O'z-o'zidan ro'yxatdan o'tish: foydalanuvchi yangi do'kon (Merchant) uchun
    ariza topshiradi ("pending" holatda). Bir foydalanuvchining bir vaqtning
    o'zida tasdiqlanishini kutayotgan (pending) do'konlari soni cheklangan —
    limitdan oshsa, admin birortasini ko'rib chiqmaguncha yangisini yaratib
    bo'lmaydi. Panelga kirish huquqi (MerchantStaffProfile) faqat admin
    do'konni tasdiqlagandan (approve) so'ng beriladi — bu `approve_merchant`da.
    """
    with transaction.atomic():
        pending_count = count_pending_merchants_for_owner(user)
        if pending_count >= MAX_PENDING_MERCHANTS_PER_OWNER:
            raise TooManyPendingMerchants()

        merchant = create_merchant(user, dict(validated_data))
    return merchant


def approve_merchant(merchant: Merchant) -> Merchant:
    """
    Admin do'konni tasdiqlaydi: status ACTIVE bo'ladi va agar egasi hali
    hech qanday do'konning xodimi bo'lmasa — unga shu do'kon uchun
    MerchantStaffProfile yaratilib, Merchant Panelga kirish ochiladi.
    """
    with transaction.atomic():
        merchant.status = MerchantStatus.ACTIVE
        merchant.save(update_fields=["status"])

        owner = merchant.owner
        if owner and not hasattr(owner, "merchant_staff_profile"):
            MerchantStaffProfile.objects.create(
                user=owner,
                merchant=merchant,
                position="Egasi",
            )
            if owner.role not in (UserRole.MERCHANT_OWNER, UserRole.MERCHANT_MANAGER):
                owner.role = UserRole.MERCHANT_OWNER
                owner.save(update_fields=["role"])
    return merchant


def reject_merchant(merchant: Merchant) -> Merchant:
    merchant.status = MerchantStatus.REJECTED
    merchant.save(update_fields=["status"])
    return merchant


def update_merchant(merchant: Merchant, validated_data: dict) -> Merchant:
    for field, value in validated_data.items():
        setattr(merchant, field, value)
    merchant.save()
    return merchant
