from rest_framework import serializers

from apps.support.models import Complaint, ComplaintMessage, Dispute, RefundRequest
from apps.support.constants import (
    ComplaintType,
    ComplaintStatus,
    DisputeStatus,
    RefundReason,
    RefundRequestStatus,
    MessageSender,
    TicketPriority,
)


# ---------------------------------------------------------------------------
# Complaint serializers
# ---------------------------------------------------------------------------


class ComplaintMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = ComplaintMessage
        fields = [
            "id",
            "sender_type",
            "sender_name",
            "body",
            "attachment",
            "is_internal",
            "created_at",
        ]
        read_only_fields = ["id", "sender_type", "sender_name", "created_at"]

    def get_sender_name(self, obj) -> str:
        if obj.sender:
            return obj.sender.get_full_name() or obj.sender.phone
        return obj.sender_type


class ComplaintListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = [
            "id",
            "public_id",
            "order_id",
            "complaint_type",
            "subject",
            "priority",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ComplaintDetailSerializer(serializers.ModelSerializer):
    messages = ComplaintMessageSerializer(many=True, read_only=True)
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = [
            "id",
            "public_id",
            "order_id",
            "complaint_type",
            "subject",
            "description",
            "priority",
            "status",
            "assigned_to_name",
            "resolution_note",
            "resolved_at",
            "messages",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_assigned_to_name(self, obj) -> str | None:
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.phone
        return None


class CreateComplaintSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    complaint_type = serializers.ChoiceField(choices=ComplaintType.choices)
    subject = serializers.CharField(max_length=255)
    description = serializers.CharField()
    priority = serializers.ChoiceField(
        choices=TicketPriority.choices,
        default=TicketPriority.MEDIUM,
    )


class AddMessageSerializer(serializers.Serializer):
    body = serializers.CharField()
    attachment = serializers.FileField(required=False, allow_null=True)
    is_internal = serializers.BooleanField(default=False)


class UpdateComplaintStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ComplaintStatus.choices)
    note = serializers.CharField(required=False, default="", allow_blank=True)


class AssignComplaintSerializer(serializers.Serializer):
    agent_id = serializers.IntegerField()
    note = serializers.CharField(required=False, default="", allow_blank=True)


# ---------------------------------------------------------------------------
# Dispute serializers
# ---------------------------------------------------------------------------


class DisputeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        fields = [
            "id",
            "order_id",
            "status",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class DisputeDetailSerializer(serializers.ModelSerializer):
    raised_by_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Dispute
        fields = [
            "id",
            "order_id",
            "complaint",
            "status",
            "description",
            "resolution_note",
            "raised_by_name",
            "assigned_to_name",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_raised_by_name(self, obj) -> str:
        return obj.raised_by.get_full_name() or obj.raised_by.phone

    def get_assigned_to_name(self, obj) -> str | None:
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.phone
        return None


class CreateDisputeSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    description = serializers.CharField()
    complaint_id = serializers.UUIDField(required=False, allow_null=True)


class UpdateDisputeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=DisputeStatus.choices)
    resolution_note = serializers.CharField(required=False, default="", allow_blank=True)
    agent_id = serializers.IntegerField(required=False, allow_null=True)


# ---------------------------------------------------------------------------
# RefundRequest serializers
# ---------------------------------------------------------------------------


class RefundRequestListSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRequest
        fields = [
            "id",
            "order_id",
            "reason",
            "amount",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RefundRequestDetailSerializer(serializers.ModelSerializer):
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = RefundRequest
        fields = [
            "id",
            "order_id",
            "complaint",
            "reason",
            "amount",
            "status",
            "review_note",
            "reviewed_by_name",
            "payment_refund_id",
            "processed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_reviewed_by_name(self, obj) -> str | None:
        if obj.reviewed_by:
            return obj.reviewed_by.get_full_name() or obj.reviewed_by.phone
        return None


class CreateRefundRequestSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    reason = serializers.ChoiceField(choices=RefundReason.choices)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    complaint_id = serializers.UUIDField(required=False, allow_null=True)


class ReviewRefundRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])
    review_note = serializers.CharField(required=False, default="", allow_blank=True)
