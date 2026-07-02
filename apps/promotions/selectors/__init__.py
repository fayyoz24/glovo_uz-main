"""
Promotions selectors – faqat READ operatsiyalari.
Barcha query shu faylda, view va service'da to'g'ridan-to'g'ri ORM yozilmaydi.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

from django.db.models import QuerySet
from django.utils import timezone

from apps.promotions.constants import PromoStatus
from apps.promotions.models import PromoCampaign, PromoUsage, ReferralCode, ReferralUsage


# ─────────────────────────── PromoCampaign ───────────────────────────────────


def get_promo_by_code(code: str) -> Optional[PromoCampaign]:
    """Kodni katta-kichik harfdan qat'iy nazar qidiradi."""
    try:
        return PromoCampaign.objects.get(code__iexact=code.strip())
    except PromoCampaign.DoesNotExist:
        return None


def get_promo_by_id(promo_id: UUID) -> Optional[PromoCampaign]:
    try:
        return PromoCampaign.objects.get(id=promo_id)
    except PromoCampaign.DoesNotExist:
        return None


def get_active_promos() -> QuerySet[PromoCampaign]:
    """Hozir amal qilayotgan barcha promo kampaniyalar."""
    now = timezone.now()
    return PromoCampaign.objects.filter(
        status=PromoStatus.ACTIVE,
        starts_at__lte=now,
    ).filter(
        models_ends_at_filter(now)
    )


def models_ends_at_filter(now):
    """ends_at null yoki kelajakda bo'lganlarni filtrlaydigan Q object."""
    from django.db.models import Q
    return Q(ends_at__isnull=True) | Q(ends_at__gt=now)


def get_promos_for_admin(
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> QuerySet[PromoCampaign]:
    qs = PromoCampaign.objects.all().order_by("-created_at")
    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(code__icontains=search) | qs.filter(name__icontains=search)
    return qs


# ─────────────────────────── PromoUsage ──────────────────────────────────────


def get_user_usage_count(promo: PromoCampaign, user_id) -> int:
    """Bir foydalanuvchi ushbu promoni necha marta ishlatgani."""
    return PromoUsage.objects.filter(promo=promo, user_id=user_id).count()


def get_promo_usages(promo_id: UUID) -> QuerySet[PromoUsage]:
    return PromoUsage.objects.filter(promo_id=promo_id).select_related("user", "order")


def has_user_used_promo(promo: PromoCampaign, user_id) -> bool:
    return PromoUsage.objects.filter(promo=promo, user_id=user_id).exists()


# ─────────────────────────── ReferralCode ────────────────────────────────────


def get_referral_code_by_user(user_id) -> Optional[ReferralCode]:
    try:
        return ReferralCode.objects.get(user_id=user_id)
    except ReferralCode.DoesNotExist:
        return None


def get_referral_code_by_code(code: str) -> Optional[ReferralCode]:
    try:
        return ReferralCode.objects.select_related("user").get(
            code__iexact=code.strip(), is_active=True
        )
    except ReferralCode.DoesNotExist:
        return None


def get_referral_usage_by_referee(user_id) -> Optional[ReferralUsage]:
    try:
        return ReferralUsage.objects.select_related("referral_code__user").get(
            referee_id=user_id
        )
    except ReferralUsage.DoesNotExist:
        return None


def get_referral_stats(user_id) -> dict:
    """Foydalanuvchining referal statistikasi."""
    referral_code = get_referral_code_by_user(user_id)
    if not referral_code:
        return {"code": None, "total_referrals": 0, "total_bonus_earned": Decimal("0")}

    usages = ReferralUsage.objects.filter(referral_code=referral_code)
    return {
        "code": referral_code.code,
        "total_referrals": usages.count(),
        "bonus_credited_count": usages.filter(referrer_bonus_credited=True).count(),
    }
