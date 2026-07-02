from rest_framework import views, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.orders.models import Order
from apps.orders.selectors import (
    get_customer_orders,
    get_order_for_customer,
    get_order_for_merchant,
    get_branch_orders,
)
from apps.orders.services import checkout_from_cart, transition_order_status, cancel_order
from apps.orders.constants import OrderStatus, CancelReason
from apps.orders.exceptions import OrderNotFound, OrderNotCancellable, InvalidOrderTransition
from apps.orders.api.serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    CheckoutSerializer,
    CancelOrderSerializer,
    MerchantOrderActionSerializer,
)
from apps.locations.models import Address  # noqa: F401 — mavjud deb faraz qilamiz


# ─── Customer Views ────────────────────────────────────────────────────────────

class CheckoutView(views.APIView):
    """POST /api/v1/orders/checkout/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        try:
            address = Address.objects.get(id=d["address_id"], user=request.user)
        except Address.DoesNotExist:
            return Response({"detail": "Manzil topilmadi."}, status=status.HTTP_400_BAD_REQUEST)

        from apps.orders.exceptions import EmptyCartError, BranchClosedError, CheckoutError
        try:
            order = checkout_from_cart(
                user=request.user,
                address=address,
                payment_method=d["payment_method"],
                tip_amount=d.get("tip_amount"),
            )
        except (EmptyCartError, BranchClosedError, CheckoutError) as e:
            return Response({"detail": str(e.detail)}, status=e.status_code)

        return Response(OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)


class CustomerOrderListView(generics.ListAPIView):
    """GET /api/v1/orders/"""
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_customer_orders(
            user=self.request.user,
            status=self.request.query_params.get("status"),
        )


class CustomerOrderDetailView(views.APIView):
    """GET /api/v1/orders/{id}/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = get_order_for_customer(pk, request.user)
        except Order.DoesNotExist:
            raise OrderNotFound()
        return Response(OrderDetailSerializer(order).data)


class CustomerOrderCancelView(views.APIView):
    """POST /api/v1/orders/{id}/cancel/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = CancelOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = Order.objects.get(id=pk, customer=request.user)
        except Order.DoesNotExist:
            raise OrderNotFound()

        try:
            order = cancel_order(
                order=order,
                reason=serializer.validated_data.get("reason", CancelReason.CUSTOMER_REQUEST),
                note=serializer.validated_data.get("note", ""),
                cancelled_by=request.user,
            )
        except OrderNotCancellable as e:
            return Response({"detail": str(e.detail)}, status=e.status_code)

        return Response(OrderDetailSerializer(order).data)


class OrderTrackView(views.APIView):
    """GET /api/v1/orders/{id}/track/ — real-time tracking uchun asosiy ma'lumot"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = get_order_for_customer(pk, request.user)
        except Order.DoesNotExist:
            raise OrderNotFound()

        courier_location = None
        if order.courier_id:
            try:
                from apps.couriers.models import CourierLocationPing
                ping = CourierLocationPing.objects.filter(
                    courier=order.courier
                ).order_by("-recorded_at").first()
                if ping:
                    courier_location = {"lat": ping.latitude, "lng": ping.longitude}
            except ImportError:
                pass

        return Response({
            "order_id": str(order.id),
            "public_id": order.public_id,
            "status": order.status,
            "merchant_name": order.merchant.name,
            "branch_name": order.branch.name,
            "courier_location": courier_location,
            "placed_at": order.placed_at,
            "estimated_delivery": None,  # Phase 2 da hisoblash qo'shiladi
        })


# ─── Merchant Panel Views ──────────────────────────────────────────────────────

class MerchantOrderListView(generics.ListAPIView):
    """GET /api/v1/merchant/orders/"""
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        branch = self.request.user.merchant_staff_profile.branch
        return get_branch_orders(
            branch=branch,
            status=self.request.query_params.get("status"),
        )


class _MerchantOrderTransitionView(views.APIView):
    """Merchant tomonidan buyurtma holati o'zgartirish (asosiy sinf)."""
    permission_classes = [IsAuthenticated]
    target_status = None

    def post(self, request, pk):
        branch = request.user.merchant_staff_profile.branch
        try:
            order = get_order_for_merchant(pk, branch)
        except Order.DoesNotExist:
            raise OrderNotFound()

        serializer = MerchantOrderActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = transition_order_status(
                order=order,
                to_status=self.target_status,
                changed_by=request.user,
                note=serializer.validated_data.get("note", ""),
            )
        except InvalidOrderTransition as e:
            return Response({"detail": str(e.detail)}, status=e.status_code)

        return Response(OrderDetailSerializer(order).data)


class MerchantConfirmOrderView(_MerchantOrderTransitionView):
    """POST /api/v1/merchant/orders/{id}/confirm/"""
    target_status = OrderStatus.MERCHANT_CONFIRMED


class MerchantRejectOrderView(views.APIView):
    """POST /api/v1/merchant/orders/{id}/reject/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        branch = request.user.merchant_staff_profile.branch
        try:
            order = get_order_for_merchant(pk, branch)
        except Order.DoesNotExist:
            raise OrderNotFound()

        try:
            order = cancel_order(
                order=order,
                reason=CancelReason.MERCHANT_REJECTED,
                note=request.data.get("note", ""),
                cancelled_by=request.user,
            )
        except OrderNotCancellable as e:
            return Response({"detail": str(e.detail)}, status=e.status_code)

        return Response(OrderDetailSerializer(order).data)


class MerchantPreparingOrderView(_MerchantOrderTransitionView):
    """POST /api/v1/merchant/orders/{id}/preparing/"""
    target_status = OrderStatus.PREPARING


class MerchantReadyOrderView(_MerchantOrderTransitionView):
    """POST /api/v1/merchant/orders/{id}/ready/"""
    target_status = OrderStatus.READY_FOR_PICKUP
