from rest_framework import views, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.dispatch.selectors import get_assignment_for_courier
from apps.dispatch.services import courier_accept_order, courier_reject_order
from apps.dispatch.services.delivery import courier_picked_up, courier_delivered
from apps.dispatch.exceptions import AssignmentNotFound, AssignmentAlreadyActioned
from apps.dispatch.api.serializers import OrderOfferSerializer, CourierAssignmentListSerializer
from apps.couriers.permissions import IsCourier, IsApprovedCourier
from apps.orders.models import Order
from apps.orders.constants import OrderStatus
from apps.orders.api.serializers import OrderDetailSerializer


class CourierAvailableOrdersView(generics.ListAPIView):
    """
    GET /api/v1/courier/orders/available/
    Kuryerga taklif qilingan va hali javob berilmagan buyurtmalar.
    """
    serializer_class = OrderOfferSerializer
    permission_classes = [IsAuthenticated, IsApprovedCourier]

    def get_queryset(self):
        from apps.dispatch.models import CourierAssignment
        from apps.dispatch.constants import AssignmentStatus
        return (
            CourierAssignment.objects
            .filter(courier=self.request.user, status=AssignmentStatus.OFFERED)
            .select_related("order__merchant", "order__branch")
            .prefetch_related("order__items")
        )


class CourierAcceptOrderView(views.APIView):
    """POST /api/v1/courier/orders/{assignment_id}/accept/"""
    permission_classes = [IsAuthenticated, IsApprovedCourier]

    def post(self, request, assignment_id):
        try:
            assignment = courier_accept_order(
                courier_user=request.user,
                assignment_id=assignment_id,
            )
        except AssignmentNotFound as e:
            return Response({"detail": str(e.detail)}, status=status.HTTP_404_NOT_FOUND)
        except AssignmentAlreadyActioned as e:
            return Response({"detail": str(e.detail)}, status=e.status_code)
        return Response(
            {"status": "accepted", "order_id": str(assignment.order_id)},
        )


class CourierRejectOrderView(views.APIView):
    """POST /api/v1/courier/orders/{assignment_id}/reject/"""
    permission_classes = [IsAuthenticated, IsApprovedCourier]

    def post(self, request, assignment_id):
        try:
            courier_reject_order(
                courier_user=request.user,
                assignment_id=assignment_id,
            )
        except AssignmentNotFound as e:
            return Response({"detail": str(e.detail)}, status=status.HTTP_404_NOT_FOUND)
        except AssignmentAlreadyActioned as e:
            return Response({"detail": str(e.detail)}, status=e.status_code)
        return Response({"status": "rejected"})


class CourierPickedUpView(views.APIView):
    """POST /api/v1/courier/orders/{order_id}/picked-up/"""
    permission_classes = [IsAuthenticated, IsApprovedCourier]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, courier=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Buyurtma topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        if order.status != OrderStatus.COURIER_ASSIGNED:
            return Response(
                {"detail": f"Buyurtma holati '{order.status}', olib ketish mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order = courier_picked_up(courier_user=request.user, order=order)
        return Response(OrderDetailSerializer(order).data)


class CourierDeliveredView(views.APIView):
    """POST /api/v1/courier/orders/{order_id}/delivered/"""
    permission_classes = [IsAuthenticated, IsApprovedCourier]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, courier=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Buyurtma topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        if order.status != OrderStatus.ON_THE_WAY:
            return Response(
                {"detail": f"Buyurtma holati '{order.status}', yetkazib bo'lmaydi."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order = courier_delivered(courier_user=request.user, order=order)
        return Response({"status": "delivered", "order_id": str(order.id)})


class CourierAssignmentHistoryView(generics.ListAPIView):
    """GET /api/v1/courier/assignments/  — kuryer tayinlash tarixi"""
    serializer_class = CourierAssignmentListSerializer
    permission_classes = [IsAuthenticated, IsCourier]

    def get_queryset(self):
        from apps.dispatch.models import CourierAssignment
        return (
            CourierAssignment.objects
            .filter(courier=self.request.user)
            .select_related("order__merchant")
            .order_by("-assigned_at")[:50]
        )
