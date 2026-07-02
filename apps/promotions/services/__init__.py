"""
Promotions services – barcha biznes logika shu yerda.
View va serializer'lar faqat shu service'larni chaqiradi.
"""
from __future__ import annotations

import random
import string
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from apps.promotions.constants import DiscountType, PromoStatus, PromoTargetType
from apps.promotions.exceptions import (
    PromoExpired,
    PromoMinOrderNotMet,
    PromoNotActive,
    PromoNotApplicableToMerchant,
    PromoNotApplicableToUser,
    PromoNotFound,
    PromoPerUserLimitReached,
    PromoUsageLimitReached,
)
from apps.promotions.models import PromoCampaign, PromoUsage, ReferralCode, ReferralUsage
from apps.promotions.selectors import (
    get_promo_by_code,
    get_referral_code_by_code,
    get_referral_code_by_user,
    get_referral_usage_by_referee,
    get_user_usage_count,
)


# ─────────────────────────── PromoService ────────────────────────────────────


class PromoService:
    """
    Promo kodlarni yaratish, tekshirish va qo'llash uchun servis.
    """

    @staticmethod
    def validate_promo(
        *,
        code: str,
        user,
        subtotal: Decimal,
        merchant_id=None,
    ) -> PromoCampaign:
        """
        Promo kodni to'liq tekshiradi.
        Muvaffaqiyatli bo'lsa PromoCampaign qaytaradi,
        aks holda mosPromoError exception chiqaradi.
        """
        promo = get_promo_by_code(code)
        if promo is None:
            raise PromoNotFound()

        if promo.status != PromoStatus.ACTIVE:
            raise PromoNotActive()

        if not promo.is_time_valid:
            raise PromoExpired()

        if not promo.is_usage_available:
            raise PromoUsageLimitReached()

        # Per-user limit
        user_usage_count = get_user_usage_count(promo=promo, user_id=user.id)
        if user_usage_count >= promo.per_user_limit:
            raise PromoPerUserLimitReached()

        # Minimal buyurtma
        if subtotal < promo.min_order_amount:
            raise PromoMinOrderNotMet(min_amount=promo.min_order_amount)

        # Merchant cheklovi
        if promo.target_type == PromoTargetType.MERCHANT:
            if not merchant_id or str(promo.merchant_id) != str(merchant_id):
                raise PromoNotApplicableToMerchant()

        # Foydalanuvchi cheklovi
        if promo.target_type == PromoTargetType.NEW_USERS:
            from apps.orders.models import Order  # FIX: to'g'ri import path
            has_orders = Order.objects.filter(customer=user).exists()
            if has_orders:
                raise PromoNotApplicableToUser()

        if promo.target_type == PromoTargetType.SPECIFIC_USERS:
            if not promo.allowed_users.filter(id=user.id).exists():
                raise PromoNotApplicableToUser()

        return promo

    @staticmethod
    def calculate_discount(
        promo: PromoCampaign,
        subtotal: Decimal,
        delivery_fee: Decimal = Decimal("0"),
    ) -> dict:
        """
        Chegirma miqdorlarini hisoblaydi.
        Returns: {
            'subtotal_discount': Decimal,
            'delivery_discount': Decimal,
            'total_discount': Decimal,
        }
        """
        subtotal_discount = Decimal("0")
        delivery_discount = Decimal("0")

        if promo.discount_type == DiscountType.FREE_DELIVERY:
            delivery_discount = delivery_fee
        else:
            subtotal_discount = promo.calculate_discount(subtotal)

        return {
            "subtotal_discount": subtotal_discount,
            "delivery_discount": delivery_discount,
            "total_discount": subtotal_discount + delivery_discount,
        }

    @staticmethod
    @transaction.atomic
    def apply_promo_to_order(
        *,
        promo: PromoCampaign,
        user,
        order,
        discount_amount: Decimal,
    ) -> PromoUsage:
        """
        Promo ishlatildi deb belgilaydi.
        Order yaratilgandan keyin chaqiriladi.
        """
        usage = PromoUsage.objects.create(
            promo=promo,
            user=user,
            order=order,
            discount_amount_applied=discount_amount,
        )

        # FIX: avvalgi siniq kod o'chirildi — to'g'ri F() expression
        from django.db.models import F
        PromoCampaign.objects.filter(pk=promo.pk).update(usage_count=F("usage_count") + 1)

        # Limit to'lganmi tekshiramiz va statusni yangilaymiz
        promo.refresh_from_db(fields=["usage_count", "usage_limit"])
        if promo.usage_limit and promo.usage_count >= promo.usage_limit:
            PromoCampaign.objects.filter(pk=promo.pk).update(status=PromoStatus.EXHAUSTED)

        return usage

    @staticmethod
    def create_campaign(*, created_by, **data) -> PromoCampaign:
        """Admin yangi kampaniya yaratadi."""
        data["code"] = data.get("code", "").upper().strip()
        data["created_by"] = created_by
        return PromoCampaign.objects.create(**data)

    @staticmethod
    def update_campaign(promo: PromoCampaign, **data) -> PromoCampaign:
        if "code" in data:
            data["code"] = data["code"].upper().strip()
        for field, value in data.items():
            setattr(promo, field, value)
        promo.save(update_fields=list(data.keys()) + ["updated_at"])
        return promo

    @staticmethod
    def pause_campaign(promo: PromoCampaign) -> PromoCampaign:
        promo.status = PromoStatus.PAUSED
        promo.save(update_fields=["status", "updated_at"])
        return promo

    @staticmethod
    def activate_campaign(promo: PromoCampaign) -> PromoCampaign:
        promo.status = PromoStatus.ACTIVE
        promo.save(update_fields=["status", "updated_at"])
        return promo


# ─────────────────────────── ReferralService ─────────────────────────────────


class ReferralService:
    """
    Referal tizimi logikasi.
    """

    REFERRAL_CODE_LENGTH = 8
    # Bu qiymatlar config/settings.py yoki DB config'dan ham olinishi mumkin
    DEFAULT_REFERRER_BONUS = Decimal("10000")   # 10,000 so'm
    DEFAULT_REFEREE_BONUS = Decimal("15000")    # 15,000 so'm

    @classmethod
    def generate_code(cls) -> str:
        """Unikal referal kod generatsiya qiladi."""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = "".join(random.choices(chars, k=cls.REFERRAL_CODE_LENGTH))
            if not ReferralCode.objects.filter(code=code).exists():
                return code

    @classmethod
    def get_or_create_referral_code(cls, user) -> ReferralCode:
        """Foydalanuvchi uchun referal kod topadi yoki yaratadi."""
        existing = get_referral_code_by_user(user.id)
        if existing:
            return existing

        return ReferralCode.objects.create(
            user=user,
            code=cls.generate_code(),
            referrer_bonus_amount=cls.DEFAULT_REFERRER_BONUS,
            referee_bonus_amount=cls.DEFAULT_REFEREE_BONUS,
        )

    @classmethod
    @transaction.atomic
    def apply_referral_on_registration(cls, *, new_user, referral_code: str) -> Optional[ReferralUsage]:
        """
        Yangi foydalanuvchi ro'yxatdan o'tganda referal kod qo'llaydi.
        Bonus birinchi buyurtmadan keyin beriladi.
        """
        # Allaqachon referal ishlatganmi
        if get_referral_usage_by_referee(new_user.id):
            return None

        referral = get_referral_code_by_code(referral_code)
        if not referral:
            return None

        # O'zining kodini ishlatmaslik
        if referral.user_id == new_user.id:
            return None

        # Limit tekshiruvi
        if referral.max_uses and referral.use_count >= referral.max_uses:
            return None

        usage = ReferralUsage.objects.create(
            referral_code=referral,
            referee=new_user,
        )

        from django.db.models import F
        ReferralCode.objects.filter(pk=referral.pk).update(use_count=F("use_count") + 1)

        return usage

    @classmethod
    @transaction.atomic
    def credit_referral_bonuses(cls, *, referee_user) -> bool:
        """
        Yangi foydalanuvchi birinchi buyurtmasini qo'yganida
        ham referrer, ham referee'ga bonus beriladi.
        Wallet / bonus tizimiga integratsiya uchun signal chiqariladi.
        """
        usage = get_referral_usage_by_referee(referee_user.id)
        if not usage:
            return False

        if usage.referee_bonus_credited:
            return False  # Allaqachon berilgan

        usage.first_order_placed_at = timezone.now()
        usage.referee_bonus_credited = True
        usage.referrer_bonus_credited = True
        usage.save(
            update_fields=[
                "first_order_placed_at",
                "referee_bonus_credited",
                "referrer_bonus_credited",
            ]
        )

        # Bonus yozish (wallet app yoki signal orqali)
        from apps.promotions.tasks import credit_referral_bonus_task  # FIX: to'g'ri import path
        credit_referral_bonus_task.delay(
            referrer_user_id=str(usage.referral_code.user_id),
            referee_user_id=str(referee_user.id),
            referrer_bonus=float(usage.referral_code.referrer_bonus_amount),
            referee_bonus=float(usage.referral_code.referee_bonus_amount),
        )

        return True
