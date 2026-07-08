from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.merchants.api.serializers import (
    MerchantListSerializer,
    MerchantDetailSerializer,
    MerchantCreateSerializer,
    MerchantBranchSerializer,
    MerchantStaffProfileSerializer,
)
from apps.merchants.selectors import (
    get_active_merchants,
    get_merchant_by_id,
    get_merchant_by_slug,
    get_merchant_branches,
    get_nearby_branches,
)
from apps.merchants.services import (
    create_merchant,
    update_merchant,
    create_branch,
    update_branch,
    toggle_accepting_orders,
)
from apps.merchants.exceptions import MerchantNotFound, BranchNotFound
from apps.common.pagination import StandardPagination
from apps.accounts.permissions import IsAdminOrSupport
from apps.merchants.permissions import IsMerchantStaff


class MerchantListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        merchant_type = request.query_params.get("type")
        merchants = get_active_merchants(merchant_type=merchant_type)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(merchants, request)
        serializer = MerchantListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MerchantDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        merchant = get_merchant_by_id(pk)
        if not merchant:
            raise MerchantNotFound()
        return Response(MerchantDetailSerializer(merchant).data)


class NearbyMerchantsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        if not lat or not lng:
            return Response({"detail": "lat and lng query params are required."}, status=400)
        branches = get_nearby_branches(float(lat), float(lng))
        serializer = MerchantBranchSerializer(branches, many=True)
        return Response(serializer.data)


class MerchantCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MerchantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        merchant = create_merchant(request.user, serializer.validated_data)
        return Response(MerchantDetailSerializer(merchant).data, status=status.HTTP_201_CREATED)


class MerchantBranchListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, merchant_pk):
        merchant = get_merchant_by_id(merchant_pk)
        if not merchant:
            raise MerchantNotFound()
        branches = get_merchant_branches(merchant_pk)
        return Response(MerchantBranchSerializer(branches, many=True).data)

    def post(self, request, merchant_pk):
        merchant = get_merchant_by_id(merchant_pk)
        if not merchant:
            raise MerchantNotFound()
        serializer = MerchantBranchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch = create_branch(merchant, serializer.validated_data)
        return Response(MerchantBranchSerializer(branch).data, status=status.HTTP_201_CREATED)


class BranchToggleOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, merchant_pk, branch_pk):
        merchant = get_merchant_by_id(merchant_pk)
        if not merchant:
            raise MerchantNotFound()
        accepting = request.data.get("accepting_orders", True)
        branch = toggle_accepting_orders(branch_pk, merchant, accepting)
        return Response(MerchantBranchSerializer(branch).data)


class MerchantStaffProfileView(APIView):
    """
    GET  /api/v1/merchant/profile/ — joriy merchant xodimining o'z profili
         (do'kon nomi, biriktirilgan filial va uning holati).
    """
    permission_classes = [IsAuthenticated, IsMerchantStaff]

    def get(self, request):
        profile = request.user.merchant_staff_profile
        return Response(MerchantStaffProfileSerializer(profile).data)


class MerchantStaffToggleAcceptingOrdersView(APIView):
    """
    POST /api/v1/merchant/branch/toggle-orders/
    { "accepting_orders": true|false }

    Merchant panelidan xodimning o'z filiali uchun buyurtma qabul qilish/
    qilmaslikni almashtiradi (o'z merchant/filialiga cheklangan — merchant_pk
    talab qilinmaydi, chunki joriy foydalanuvchining biriktirilgan filiali olinadi).
    """
    permission_classes = [IsAuthenticated, IsMerchantStaff]

    def post(self, request):
        profile = request.user.merchant_staff_profile
        if profile.branch is None:
            return Response({"detail": "Sizga hech qanday filial biriktirilmagan."}, status=400)
        accepting = request.data.get("accepting_orders", True)
        branch = toggle_accepting_orders(profile.branch_id, profile.merchant, accepting)
        return Response(MerchantBranchSerializer(branch).data)
