import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order
from apps.payments.models import PaymentTransaction, Refund
from apps.payments.serializers import (
    InitiatePaymentSerializer,
    PaymentTransactionSerializer,
    RefundRequestSerializer,
    RefundSerializer,
)
from apps.payments.services import (
    confirm_cash_payment,
    get_transaction_detail,
    get_transaction_list,
    initiate_payment,
    process_refund,
    request_refund,
)

logger = logging.getLogger(__name__)


class InitiatePaymentView(APIView):
    """
    POST /api/payments/initiate/
    Start payment for an order. Returns transaction + payment_url (for Click/Payme).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]
        provider = serializer.validated_data["provider"]

        try:
            order = Order.objects.get(id=order_id, customer=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Buyurtma topilmadi."}, status=404)

        try:
            txn = initiate_payment(order, provider)
        except Exception as e:
            logger.warning("initiate_payment error: %s", e)
            return Response({"detail": str(e)}, status=400)

        return Response(PaymentTransactionSerializer(txn).data, status=201)


class PaymentTransactionListView(APIView):
    """
    GET /api/payments/transactions/?order_id=<uuid>
    List transactions for an order.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        order_id = request.query_params.get("order_id")
        if not order_id:
            return Response({"detail": "order_id talab qilinadi."}, status=400)

        try:
            order = Order.objects.get(id=order_id, customer=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Buyurtma topilmadi."}, status=404)

        txns = get_transaction_list(order)
        return Response(PaymentTransactionSerializer(txns, many=True).data)


class PaymentTransactionDetailView(APIView):
    """
    GET /api/payments/transactions/<uuid>/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            txn = get_transaction_detail(pk, user=request.user)
        except PaymentTransaction.DoesNotExist:
            return Response({"detail": "Transaction topilmadi."}, status=404)
        return Response(PaymentTransactionSerializer(txn).data)


class ConfirmCashPaymentView(APIView):
    """
    POST /api/payments/cash/confirm/
    Admin/courier marks cash as received.
    Body: { "order_id": "<uuid>" }
    """

    permission_classes = [IsAdminUser]

    def post(self, request):
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"detail": "order_id talab qilinadi."}, status=400)

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Buyurtma topilmadi."}, status=404)

        try:
            txn = confirm_cash_payment(order)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)

        return Response(PaymentTransactionSerializer(txn).data)


class RefundRequestView(APIView):
    """
    POST /api/payments/refund/
    Customer or admin requests a refund.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]
        amount = serializer.validated_data["amount"]
        reason = serializer.validated_data["reason"]

        try:
            order = Order.objects.get(id=order_id)
            # Only customer or admin can refund
            if not request.user.is_staff and order.customer != request.user:
                return Response({"detail": "Ruxsat yo'q."}, status=403)
        except Order.DoesNotExist:
            return Response({"detail": "Buyurtma topilmadi."}, status=404)

        try:
            refund = request_refund(order, amount, reason)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)

        return Response(RefundSerializer(refund).data, status=201)


class ProcessRefundView(APIView):
    """
    POST /api/payments/refund/<uuid>/process/
    Admin triggers actual refund processing.
    """

    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        try:
            refund = Refund.objects.get(id=pk)
        except Refund.DoesNotExist:
            return Response({"detail": "Refund topilmadi."}, status=404)

        try:
            process_refund(refund)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)

        return Response(RefundSerializer(refund).data)


# ------------------------------------------------------------------
# Click callbacks — called by Click servers, no user auth
# ------------------------------------------------------------------

class ClickPrepareView(APIView):
    """
    POST /api/payments/click/prepare/
    Called by Click to verify the order before charging.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # Click uses signature-based auth

    def post(self, request):
        from apps.payments.providers.click import handle_prepare

        data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
        # Flatten single-value lists (form-encoded)
        flat = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in data.items()}

        logger.info("Click PREPARE: %s", flat)
        result = handle_prepare(flat)
        return Response(result)


class ClickCompleteView(APIView):
    """
    POST /api/payments/click/complete/
    Called by Click after payment confirmation.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        from apps.payments.providers.click import handle_complete

        data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
        flat = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in data.items()}

        logger.info("Click COMPLETE: %s", flat)
        result = handle_complete(flat)
        return Response(result)


# ------------------------------------------------------------------
# Payme callbacks — single endpoint, JSON-RPC
# ------------------------------------------------------------------

class PaymeCallbackView(APIView):
    """
    POST /api/payments/payme/
    Single JSON-RPC endpoint for all Payme methods.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        from apps.payments.providers.payme import dispatch, verify_auth

        if not verify_auth(request):
            return Response(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32504, "message": "Insufficient privileges"},
                },
                status=403,
            )

        body = request.data
        request_id = body.get("id")
        params = body.get("params", {})

        logger.info("Payme method=%s", body.get("method"))
        result = dispatch(body, request_id, params)
        return Response(result)
