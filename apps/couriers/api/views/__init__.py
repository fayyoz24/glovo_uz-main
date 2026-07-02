from rest_framework import views, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.couriers.selectors import (
    get_courier_profile,
    get_courier_earnings_summary,
    get_courier_earnings_list,
    get_active_shift,
)
from apps.couriers.services import go_online, go_offline, record_location_ping
from apps.couriers.exceptions import (
    CourierProfileNotFound,
    CourierAlreadyOnline,
    CourierAlreadyOffline,
    CourierNotOnline,
    ActiveShiftExists,
)
from apps.couriers.api.serializers import (
    CourierProfileSerializer,
    CourierProfileUpdateSerializer,
    LocationPingSerializer,
    CourierShiftSerializer,
    CourierEarningSerializer,
    EarningsSummarySerializer,
)
from apps.couriers.permissions import IsCourier


class CourierProfileView(views.APIView):
    """GET/PATCH /api/v1/courier/profile/"""
    permission_classes = [IsAuthenticated, IsCourier]

    def get(self, request):
        profile = get_courier_profile(request.user)
        return Response(CourierProfileSerializer(profile).data)

    def patch(self, request):
        profile = get_courier_profile(request.user)
        serializer = CourierProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CourierProfileSerializer(profile).data)


class CourierGoOnlineView(views.APIView):
    """POST /api/v1/courier/go-online/"""
    permission_classes = [IsAuthenticated, IsCourier]

    def post(self, request):
        try:
            profile = go_online(user=request.user)
        except (CourierAlreadyOnline, ActiveShiftExists) as e:
            return Response({"detail": str(e.detail)}, status=e.status_code)
        return Response(CourierProfileSerializer(profile).data)


class CourierGoOfflineView(views.APIView):
    """POST /api/v1/courier/go-offline/"""
    permission_classes = [IsAuthenticated, IsCourier]

    def post(self, request):
        try:
            profile = go_offline(user=request.user)
        except CourierAlreadyOffline as e:
            return Response({"detail": str(e.detail)}, status=e.status_code)
        return Response(CourierProfileSerializer(profile).data)


class CourierLocationPingView(views.APIView):
    """POST /api/v1/courier/location-ping/"""
    permission_classes = [IsAuthenticated, IsCourier]

    def post(self, request):
        serializer = LocationPingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        record_location_ping(
            user=request.user,
            latitude=float(d["latitude"]),
            longitude=float(d["longitude"]),
            accuracy=d.get("accuracy"),
        )
        return Response({"status": "ok"})


class CourierActiveOrdersView(views.APIView):
    """GET /api/v1/courier/orders/  — kuryerning faol buyurtmalari"""
    permission_classes = [IsAuthenticated, IsCourier]

    def get(self, request):
        from apps.orders.selectors import get_active_orders_for_courier
        from apps.orders.api.serializers import OrderListSerializer
        orders = get_active_orders_for_courier(request.user)
        return Response(OrderListSerializer(orders, many=True).data)


class CourierEarningsView(views.APIView):
    """GET /api/v1/courier/earnings/"""
    permission_classes = [IsAuthenticated, IsCourier]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        summary = get_courier_earnings_summary(request.user, days=days)
        earnings = get_courier_earnings_list(request.user)
        return Response({
            "summary": EarningsSummarySerializer(summary).data,
            "history": CourierEarningSerializer(earnings, many=True).data,
        })


class CourierShiftView(views.APIView):
    """GET /api/v1/courier/shift/  — joriy smena"""
    permission_classes = [IsAuthenticated, IsCourier]

    def get(self, request):
        shift = get_active_shift(request.user)
        if shift is None:
            return Response({"detail": "Faol smena yo'q."}, status=status.HTTP_404_NOT_FOUND)
        return Response(CourierShiftSerializer(shift).data)
