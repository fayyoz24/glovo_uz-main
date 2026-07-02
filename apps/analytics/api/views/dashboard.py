from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.analytics.permissions.analytics import IsAdminAnalytics
from apps.analytics.constants.analytics import AnalyticsPeriod, resolve_period
from apps.analytics.api.serializers.dashboard import AnalyticsQuerySerializer
from apps.analytics.selectors.dashboard import (
    get_dashboard_overview, get_dashboard_order_status_breakdown,
    get_dashboard_payment_summary, get_dashboard_delivery_metrics,
)
from apps.analytics.selectors.orders import (
    get_orders_summary, get_orders_timeseries, get_avg_delivery_time, get_order_status_breakdown,
)
from apps.analytics.selectors.revenue import (
    get_revenue_summary, get_revenue_by_day, get_payment_provider_breakdown,
)
from apps.analytics.selectors.merchants import (
    get_merchant_summary, get_top_merchants_by_orders, get_top_merchants_by_revenue, get_low_performing_merchants,
)
from apps.analytics.selectors.couriers import get_courier_summary, get_top_couriers, get_courier_delivery_metrics


class AnalyticsBaseAPIView(APIView):
    permission_classes = [IsAdminAnalytics]

    def get_period(self, request):
        serializer = AnalyticsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data.get("period", AnalyticsPeriod.WEEK) == AnalyticsPeriod.CUSTOM:
            return data["start_date"], data["end_date"]
        return resolve_period(data.get("period", AnalyticsPeriod.WEEK))


class AdminDashboardFullAPIView(AnalyticsBaseAPIView):
    def get(self, request, *args, **kwargs):
        start_date, end_date = self.get_period(request)
        return Response({
            "overview": get_dashboard_overview(start_date, end_date),
            "order_status_breakdown": get_dashboard_order_status_breakdown(start_date, end_date),
            "payment_summary": get_dashboard_payment_summary(start_date, end_date),
            "delivery_metrics": get_dashboard_delivery_metrics(start_date, end_date),
        }, status=status.HTTP_200_OK)


class AdminDashboardOverviewAPIView(AnalyticsBaseAPIView):
    def get(self, request, *args, **kwargs):
        start_date, end_date = self.get_period(request)
        return Response(get_dashboard_overview(start_date, end_date), status=status.HTTP_200_OK)


class AdminDashboardOrdersAPIView(AnalyticsBaseAPIView):
    def get(self, request, *args, **kwargs):
        start_date, end_date = self.get_period(request)
        return Response({
            "summary": get_orders_summary(start_date, end_date),
            "status_breakdown": get_order_status_breakdown(start_date, end_date),
            "timeseries": get_orders_timeseries(start_date, end_date),
            "avg_delivery_minutes": get_avg_delivery_time(start_date, end_date),
        })


class AdminDashboardRevenueAPIView(AnalyticsBaseAPIView):
    def get(self, request, *args, **kwargs):
        start_date, end_date = self.get_period(request)
        return Response({
            "summary": get_revenue_summary(start_date, end_date),
            "revenue_by_day": get_revenue_by_day(start_date, end_date),
            "provider_breakdown": get_payment_provider_breakdown(start_date, end_date),
        })


class AdminDashboardMerchantsAPIView(AnalyticsBaseAPIView):
    def get(self, request, *args, **kwargs):
        start_date, end_date = self.get_period(request)
        return Response({
            "summary": get_merchant_summary(start_date, end_date),
            "top_by_orders": get_top_merchants_by_orders(start_date, end_date),
            "top_by_revenue": get_top_merchants_by_revenue(start_date, end_date),
            "low_performing": get_low_performing_merchants(start_date, end_date),
        })


class AdminDashboardCouriersAPIView(AnalyticsBaseAPIView):
    def get(self, request, *args, **kwargs):
        start_date, end_date = self.get_period(request)
        return Response({
            "summary": get_courier_summary(start_date, end_date),
            "top_couriers": get_top_couriers(start_date, end_date),
            "delivery_metrics": get_courier_delivery_metrics(start_date, end_date),
        })
