from rest_framework import serializers

from apps.payments.models import PaymentProvider, PaymentTransaction, Refund


class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    provider = serializers.ChoiceField(choices=PaymentProvider.choices)


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "order",
            "provider",
            "amount",
            "currency",
            "status",
            "payment_url",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RefundRequestSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    reason = serializers.CharField(max_length=500)


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = [
            "id",
            "order",
            "transaction",
            "amount",
            "reason",
            "status",
            "created_at",
            "processed_at",
        ]
        read_only_fields = fields


class ClickCallbackSerializer(serializers.Serializer):
    """Validates incoming Click callback fields."""
    click_trans_id = serializers.CharField()
    service_id = serializers.CharField()
    click_paydoc_id = serializers.CharField(required=False, allow_blank=True)
    merchant_trans_id = serializers.CharField()
    merchant_prepare_id = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    action = serializers.IntegerField()
    error = serializers.IntegerField()
    error_note = serializers.CharField(required=False, allow_blank=True)
    sign_time = serializers.CharField()
    sign_string = serializers.CharField()
