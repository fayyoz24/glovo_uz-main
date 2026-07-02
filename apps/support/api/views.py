from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.support.api.serializers import (
    AddMessageSerializer,
    AssignComplaintSerializer,
    ComplaintDetailSerializer,
    ComplaintListSerializer,
    ComplaintMessageSerializer,
    CreateComplaintSerializer,
    CreateDisputeSerializer,
    CreateRefundRequestSerializer,
    DisputeDetailSerializer,
    DisputeListSerializer,
    RefundRequestDetailSerializer,
    RefundRequestListSerializer,
    ReviewRefundRequestSerializer,
    UpdateComplaintStatusSerializer,
    UpdateDisputeSerializer,
)
from apps.support.constants import MessageSender
from apps.support.exceptions import (
    ComplaintNotFound,
    DisputeNotFound,
    RefundRequestNotFound,
)
from apps.support.permissions import (
    IsComplaintOwnerOrSupport,
    IsRefundRequestOwnerOrSupport,
    IsSupportAgent,
)
from apps.support.selectors import (
    get_all_complaints,
    get_all_disputes,
    get_all_refund_requests,
    get_complaint_by_id,
    get_complaint_with_messages,
    get_complaints_for_customer,
    get_dispute_by_id,
    get_disputes_for_order,
    get_messages_for_complaint,
    get_refund_request_by_id,
    get_refund_requests_for_customer,
)
from apps.support.services import (
    add_complaint_message,
    approve_refund_request,
    assign_complaint,
    create_complaint,
    create_dispute,
    create_refund_request,
    reject_refund_request,
    update_complaint_status,
    update_dispute_status,
)


# ---------------------------------------------------------------------------
# Customer complaint views
# ---------------------------------------------------------------------------


class CustomerComplaintViewSet(GenericViewSet):
    """
    Endpoints for customers to manage their own complaints.

    list:   GET  /api/v1/support/complaints/
    create: POST /api/v1/support/complaints/
    retrieve: GET /api/v1/support/complaints/{id}/
    messages: GET /api/v1/support/complaints/{id}/messages/
    reply:  POST /api/v1/support/complaints/{id}/reply/
    """

    permission_classes = [IsAuthenticated, IsComplaintOwnerOrSupport]

    def list(self, request):
        status_filter = request.query_params.get("status")
        complaints = get_complaints_for_customer(
            user_id=request.user.id,
            status=status_filter,
        )
        serializer = ComplaintListSerializer(complaints, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = CreateComplaintSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        complaint = create_complaint(
            customer_id=request.user.id,
            **serializer.validated_data,
        )
        return Response(
            ComplaintDetailSerializer(complaint).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        complaint = get_complaint_with_messages(complaint_id=pk)
        if not complaint:
            raise ComplaintNotFound()
        self.check_object_permissions(request, complaint)
        include_internal = request.user.is_staff or getattr(request.user, "role", None) in ("admin", "support")
        # Filter out internal messages for customers
        if not include_internal:
            complaint._prefetched_objects_cache["messages"] = [
                m for m in complaint.messages.all() if not m.is_internal
            ]
        return Response(ComplaintDetailSerializer(complaint).data)

    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        complaint = get_complaint_by_id(complaint_id=pk)
        if not complaint:
            raise ComplaintNotFound()
        self.check_object_permissions(request, complaint)
        is_support = request.user.is_staff or getattr(request.user, "role", None) in ("admin", "support")
        messages = get_messages_for_complaint(
            complaint_id=pk,
            include_internal=is_support,
        )
        return Response(ComplaintMessageSerializer(messages, many=True).data)

    @action(detail=True, methods=["post"], url_path="reply")
    def reply(self, request, pk=None):
        complaint = get_complaint_by_id(complaint_id=pk)
        if not complaint:
            raise ComplaintNotFound()
        self.check_object_permissions(request, complaint)

        serializer = AddMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        is_support = request.user.is_staff or getattr(request.user, "role", None) in ("admin", "support")
        sender_type = MessageSender.SUPPORT if is_support else MessageSender.CUSTOMER

        # Only support agents can send internal messages
        is_internal = data.get("is_internal", False) and is_support

        message = add_complaint_message(
            complaint=complaint,
            sender_id=request.user.id,
            sender_type=sender_type,
            body=data["body"],
            is_internal=is_internal,
            attachment=data.get("attachment"),
        )
        return Response(
            ComplaintMessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Support agent / admin complaint views
# ---------------------------------------------------------------------------


class AdminComplaintViewSet(GenericViewSet):
    """
    Admin/support endpoints for managing all complaints.

    list:     GET  /api/v1/admin/support/complaints/
    retrieve: GET  /api/v1/admin/support/complaints/{id}/
    update_status: POST /api/v1/admin/support/complaints/{id}/update-status/
    assign:   POST /api/v1/admin/support/complaints/{id}/assign/
    """

    permission_classes = [IsAuthenticated, IsSupportAgent]

    def list(self, request):
        status_filter = request.query_params.get("status")
        priority_filter = request.query_params.get("priority")
        assigned_to = request.query_params.get("assigned_to")

        complaints = get_all_complaints(
            status=status_filter,
            priority=priority_filter,
            assigned_to_id=assigned_to,
        )
        serializer = ComplaintListSerializer(complaints, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        complaint = get_complaint_with_messages(complaint_id=pk)
        if not complaint:
            raise ComplaintNotFound()
        return Response(ComplaintDetailSerializer(complaint).data)

    @action(detail=True, methods=["post"], url_path="update-status")
    def update_status(self, request, pk=None):
        complaint = get_complaint_by_id(complaint_id=pk)
        if not complaint:
            raise ComplaintNotFound()

        serializer = UpdateComplaintStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = update_complaint_status(
            complaint=complaint,
            new_status=serializer.validated_data["status"],
            agent_id=request.user.id,
            note=serializer.validated_data.get("note", ""),
        )
        return Response(ComplaintDetailSerializer(updated).data)

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        complaint = get_complaint_by_id(complaint_id=pk)
        if not complaint:
            raise ComplaintNotFound()

        serializer = AssignComplaintSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = assign_complaint(
            complaint=complaint,
            agent_id=serializer.validated_data["agent_id"],
            note=serializer.validated_data.get("note", ""),
        )
        return Response(ComplaintDetailSerializer(updated).data)


# ---------------------------------------------------------------------------
# Dispute views
# ---------------------------------------------------------------------------


class DisputeViewSet(GenericViewSet):
    """
    Disputes for escalated cases.

    customer list:   GET  /api/v1/support/disputes/
    customer create: POST /api/v1/support/disputes/
    admin list:      GET  /api/v1/admin/support/disputes/
    admin update:    POST /api/v1/admin/support/disputes/{id}/update/
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        is_admin = request.user.is_staff or getattr(request.user, "role", None) in ("admin", "support")
        if is_admin:
            status_filter = request.query_params.get("status")
            disputes = get_all_disputes(status=status_filter)
        else:
            order_id = request.query_params.get("order_id")
            if not order_id:
                return Response({"detail": "order_id query param required."}, status=400)
            disputes = get_disputes_for_order(order_id=order_id)
        return Response(DisputeListSerializer(disputes, many=True).data)

    def create(self, request):
        serializer = CreateDisputeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dispute = create_dispute(
            order_id=serializer.validated_data["order_id"],
            raised_by_id=request.user.id,
            description=serializer.validated_data["description"],
            complaint_id=serializer.validated_data.get("complaint_id"),
        )
        return Response(
            DisputeDetailSerializer(dispute).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        dispute = get_dispute_by_id(dispute_id=pk)
        if not dispute:
            raise DisputeNotFound()
        return Response(DisputeDetailSerializer(dispute).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="update",
        permission_classes=[IsAuthenticated, IsSupportAgent],
    )
    def update_dispute(self, request, pk=None):
        dispute = get_dispute_by_id(dispute_id=pk)
        if not dispute:
            raise DisputeNotFound()

        serializer = UpdateDisputeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        updated = update_dispute_status(
            dispute=dispute,
            new_status=data["status"],
            agent_id=data.get("agent_id") or request.user.id,
            resolution_note=data.get("resolution_note", ""),
        )
        return Response(DisputeDetailSerializer(updated).data)


# ---------------------------------------------------------------------------
# Refund request views
# ---------------------------------------------------------------------------


class RefundRequestViewSet(GenericViewSet):
    """
    Customer: list, create their refund requests.
    Admin:    list all, approve/reject.

    GET  /api/v1/support/refunds/
    POST /api/v1/support/refunds/
    GET  /api/v1/support/refunds/{id}/
    POST /api/v1/admin/support/refunds/{id}/review/
    """

    permission_classes = [IsAuthenticated, IsRefundRequestOwnerOrSupport]

    def list(self, request):
        is_admin = request.user.is_staff or getattr(request.user, "role", None) in ("admin", "support")
        if is_admin:
            status_filter = request.query_params.get("status")
            refunds = get_all_refund_requests(status=status_filter)
        else:
            status_filter = request.query_params.get("status")
            refunds = get_refund_requests_for_customer(
                user_id=request.user.id,
                status=status_filter,
            )
        return Response(RefundRequestListSerializer(refunds, many=True).data)

    def create(self, request):
        serializer = CreateRefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        refund = create_refund_request(
            order_id=data["order_id"],
            customer_id=request.user.id,
            reason=data["reason"],
            amount=data["amount"],
            complaint_id=data.get("complaint_id"),
        )
        return Response(
            RefundRequestDetailSerializer(refund).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        refund = get_refund_request_by_id(refund_id=pk)
        if not refund:
            raise RefundRequestNotFound()
        self.check_object_permissions(request, refund)
        return Response(RefundRequestDetailSerializer(refund).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="review",
        permission_classes=[IsAuthenticated, IsSupportAgent],
    )
    def review(self, request, pk=None):
        refund = get_refund_request_by_id(refund_id=pk)
        if not refund:
            raise RefundRequestNotFound()

        serializer = ReviewRefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action_type = serializer.validated_data["action"]
        note = serializer.validated_data.get("review_note", "")

        if action_type == "approve":
            updated = approve_refund_request(
                refund_request=refund,
                reviewed_by_id=request.user.id,
                review_note=note,
            )
        else:
            updated = reject_refund_request(
                refund_request=refund,
                reviewed_by_id=request.user.id,
                review_note=note,
            )
        return Response(RefundRequestDetailSerializer(updated).data)
