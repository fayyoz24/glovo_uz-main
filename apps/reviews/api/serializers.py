from rest_framework import serializers

from apps.reviews.models import Review, ReviewFlag, ReviewImage
from apps.reviews.models.review_flag import FlagReason


# ──────────────────────────── Nested ─────────────────────────────────────────


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ["id", "image", "sort_order"]


# ──────────────────────────── Customer ───────────────────────────────────────


class ReviewCreateSerializer(serializers.Serializer):
    """POST /api/v1/orders/{id}/review/"""

    merchant_rating = serializers.IntegerField(min_value=1, max_value=5)
    merchant_comment = serializers.CharField(
        max_length=1000, required=False, allow_blank=True, default=""
    )
    courier_rating = serializers.IntegerField(
        min_value=1, max_value=5, required=False, allow_null=True
    )
    courier_comment = serializers.CharField(
        max_length=1000, required=False, allow_blank=True, default=""
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        max_length=5,
    )


class ReviewUpdateSerializer(serializers.Serializer):
    """PATCH /api/v1/reviews/{id}/"""

    merchant_rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    merchant_comment = serializers.CharField(
        max_length=1000, required=False, allow_blank=True
    )
    courier_rating = serializers.IntegerField(
        min_value=1, max_value=5, required=False, allow_null=True
    )
    courier_comment = serializers.CharField(
        max_length=1000, required=False, allow_blank=True
    )


class ReviewDetailSerializer(serializers.ModelSerializer):
    """Mijoz o'z reviewini ko'rish uchun."""

    images = ReviewImageSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    merchant_name = serializers.CharField(source="merchant.name", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "order",
            "customer_name",
            "merchant_name",
            "merchant_rating",
            "merchant_comment",
            "courier_rating",
            "courier_comment",
            "merchant_reply",
            "merchant_replied_at",
            "images",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class MerchantReviewListSerializer(serializers.ModelSerializer):
    """Do'kon sahifasida ko'rinadigan reviewlar."""

    images = ReviewImageSerializer(many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "customer_name",
            "merchant_rating",
            "merchant_comment",
            "merchant_reply",
            "merchant_replied_at",
            "images",
            "created_at",
        ]

    def get_customer_name(self, obj) -> str:
        """Mijoz ismini qisman ko'rsatish (maxfiylik)."""
        name = obj.customer.full_name or ""
        if len(name) > 1:
            return name[0] + "*" * (len(name) - 1)
        return name or "Anonim"


class MerchantRatingStatsSerializer(serializers.Serializer):
    avg_rating = serializers.FloatField()
    total_count = serializers.IntegerField()
    distribution = serializers.DictField(child=serializers.IntegerField())


# ──────────────────────────── Merchant panel ─────────────────────────────────


class MerchantReplySerializer(serializers.Serializer):
    """POST /api/v1/merchant/reviews/{id}/reply/"""

    reply_text = serializers.CharField(max_length=1000)


# ──────────────────────────── Flag ───────────────────────────────────────────


class ReviewFlagSerializer(serializers.Serializer):
    """POST /api/v1/reviews/{id}/flag/"""

    reason = serializers.ChoiceField(choices=FlagReason.choices)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


# ──────────────────────────── Admin ──────────────────────────────────────────


class AdminReviewListSerializer(serializers.ModelSerializer):
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)
    merchant_name = serializers.CharField(source="merchant.name", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "customer_phone",
            "merchant_name",
            "merchant_rating",
            "courier_rating",
            "status",
            "flag_count",
            "created_at",
        ]


class AdminReviewDetailSerializer(serializers.ModelSerializer):
    images = ReviewImageSerializer(many=True, read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)
    merchant_name = serializers.CharField(source="merchant.name", read_only=True)

    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminModerationSerializer(serializers.Serializer):
    """Admin review hide/restore qilganda."""

    note = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
