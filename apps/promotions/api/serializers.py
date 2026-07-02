from decimal import Decimal

from rest_framework import serializers

from apps.promotions.models import PromoCampaign, PromoUsage, ReferralCode


# ─────────────────────────── Customer-facing ─────────────────────────────────


class PromoValidateSerializer(serializers.Serializer):
    """
    Cart'da promo kodni tekshirish uchun.
    POST /api/v1/cart/apply-promo/
    """

    code = serializers.CharField(max_length=50)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    merchant_id = serializers.UUIDField(required=False, allow_null=True)


class PromoDiscountResponseSerializer(serializers.Serializer):
    """Promo qo'llangandan keyin qaytariladigan ma'lumot."""

    code = serializers.CharField()
    discount_type = serializers.CharField()
    discount_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    subtotal_discount = serializers.DecimalField(max_digits=12, decimal_places=2)
    delivery_discount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_discount = serializers.DecimalField(max_digits=12, decimal_places=2)
    message = serializers.CharField()


# ─────────────────────────── Admin serializers ───────────────────────────────


class PromoCampaignListSerializer(serializers.ModelSerializer):
    """Admin ro'yxat ko'rinishi uchun."""

    class Meta:
        model = PromoCampaign
        fields = [
            "id",
            "name",
            "code",
            "discount_type",
            "discount_value",
            "status",
            "starts_at",
            "ends_at",
            "usage_count",
            "usage_limit",
        ]


class PromoCampaignDetailSerializer(serializers.ModelSerializer):
    """Admin to'liq ma'lumot uchun."""

    class Meta:
        model = PromoCampaign
        fields = "__all__"
        read_only_fields = ["id", "usage_count", "created_at", "updated_at", "created_by"]


class PromoCampaignCreateSerializer(serializers.ModelSerializer):
    """Admin yangi kampaniya yaratish uchun."""

    class Meta:
        model = PromoCampaign
        fields = [
            "name",
            "description",
            "code",
            "discount_type",
            "discount_value",
            "max_discount",
            "min_order_amount",
            "usage_limit",
            "per_user_limit",
            "starts_at",
            "ends_at",
            "target_type",
            "merchant",
            "is_combinable",
            "applies_to_delivery_fee",
            "status",
        ]

    def validate_code(self, value: str) -> str:
        return value.upper().strip()

    def validate(self, data: dict) -> dict:
        discount_type = data.get("discount_type")
        discount_value = data.get("discount_value", Decimal("0"))

        if discount_type == "percentage" and discount_value > 100:
            raise serializers.ValidationError(
                {"discount_value": "Foiz 100 dan oshmasligi kerak."}
            )
        return data


class PromoCampaignUpdateSerializer(PromoCampaignCreateSerializer):
    """Admin kampaniyani tahrirlash uchun – hamma maydon ixtiyoriy."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


class PromoUsageSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    order_public_id = serializers.CharField(source="order.public_id", read_only=True)

    class Meta:
        model = PromoUsage
        fields = [
            "id",
            "user_phone",
            "order_public_id",
            "discount_amount_applied",
            "used_at",
        ]


# ─────────────────────────── Referral ────────────────────────────────────────


class ReferralCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralCode
        fields = [
            "code",
            "referrer_bonus_amount",
            "referee_bonus_amount",
            "use_count",
        ]
        read_only_fields = fields


class ReferralApplySerializer(serializers.Serializer):
    """Ro'yxatdan o'tishda referal kod kiritish."""

    referral_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
