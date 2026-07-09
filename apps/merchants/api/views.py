from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.merchants.models import Merchant
from apps.merchants.api.serializers import (
    MerchantListSerializer,
    MerchantDetailSerializer,
    MerchantCreateSerializer,
    MerchantUpdateSerializer,
    MerchantBranchSerializer,
    MerchantStaffProfileSerializer,
)
from apps.merchants.selectors import (
    get_active_merchants,
    get_merchant_by_id,
    get_merchant_by_slug,
    get_merchant_branches,
    get_branch_by_id,
    get_nearby_branches,
    get_merchants_owned_by,
    get_pending_merchants,
)
from apps.merchants.services import (
    create_merchant,
    register_merchant_with_owner,
    approve_merchant,
    reject_merchant,
    update_merchant,
    create_branch,
    update_branch,
    toggle_accepting_orders,
)
from apps.merchants.services.merchant import MAX_PENDING_MERCHANTS_PER_OWNER
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


class MerchantSelfRegisterView(APIView):
    """
    POST /api/v1/merchant/register/
    { "name": "...", "type": "food", "description": "..." }

    Har qanday login qilgan foydalanuvchi o'z do'koni uchun ariza topshiradi.
    Do'kon "pending" holatda yaratiladi — admin uni tasdiqlamaguncha (approve)
    Merchant Panelga kirish va mahsulot qo'shish imkoni ochilmaydi. Bitta
    foydalanuvchining bir vaqtda tasdiqlanishini kutayotgan (pending)
    do'konlari soni {max_pending} tadan oshmasligi kerak.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MerchantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        merchant = register_merchant_with_owner(request.user, serializer.validated_data)
        return Response(MerchantDetailSerializer(merchant).data, status=status.HTTP_201_CREATED)


class MyMerchantApplicationsView(APIView):
    """
    GET /api/v1/merchant/applications/

    Foydalanuvchi topshirgan barcha do'kon arizalari va ularning holati
    (pending / active / rejected) — hali panelga kirish huquqi bo'lmagan
    foydalanuvchilar uchun "kuting" ekranida ko'rsatiladi.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        merchants = get_merchants_owned_by(request.user)
        return Response({
            "applications": MerchantDetailSerializer(merchants, many=True).data,
            "pending_count": sum(1 for m in merchants if m.status == "pending"),
            "max_pending": MAX_PENDING_MERCHANTS_PER_OWNER,
            "has_active_panel": hasattr(request.user, "merchant_staff_profile"),
        })


class MyMerchantView(APIView):
    """
    GET   /api/v1/merchant/mine/ — do'konimning to'liq ma'lumoti (filiallari bilan)
    PATCH /api/v1/merchant/mine/ — do'kon ma'lumotlarini tahrirlash
    """
    permission_classes = [IsAuthenticated, IsMerchantStaff]

    def get(self, request):
        merchant = request.user.merchant_staff_profile.merchant
        return Response(MerchantDetailSerializer(merchant).data)

    def patch(self, request):
        merchant = request.user.merchant_staff_profile.merchant
        serializer = MerchantUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        merchant = update_merchant(merchant, serializer.validated_data)
        return Response(MerchantDetailSerializer(merchant).data)


class MyBranchView(APIView):
    """
    POST  /api/v1/merchant/branch/ — o'zimga birinchi filialni yaratish
          (agar hali filialim bo'lmasa; yaratilgach avtomatik profilimga biriktiriladi)
    PATCH /api/v1/merchant/branch/ — o'z filialim ma'lumotlarini tahrirlash
    """
    permission_classes = [IsAuthenticated, IsMerchantStaff]

    def post(self, request):
        profile = request.user.merchant_staff_profile
        if profile.branch is not None:
            return Response(
                {"detail": "Sizda allaqachon filial mavjud."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = MerchantBranchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch = create_branch(profile.merchant, serializer.validated_data)
        profile.branch = branch
        profile.save(update_fields=["branch"])
        return Response(MerchantBranchSerializer(branch).data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        profile = request.user.merchant_staff_profile
        if profile.branch is None:
            return Response({"detail": "Sizga hech qanday filial biriktirilmagan."}, status=400)
        serializer = MerchantBranchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        branch = update_branch(profile.branch_id, profile.merchant, serializer.validated_data)
        return Response(MerchantBranchSerializer(branch).data)


class BranchToggleOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, merchant_pk, branch_pk):
        merchant = get_merchant_by_id(merchant_pk)
        if not merchant:
            raise MerchantNotFound()
        accepting = request.data.get("accepting_orders", True)
        branch = toggle_accepting_orders(branch_pk, merchant, accepting)
        return Response(MerchantBranchSerializer(branch).data)


class MyBranchesView(APIView):
    """
    GET  /api/v1/merchant/branches/ — do'konimning barcha filiallari ro'yxati
    POST /api/v1/merchant/branches/ — qo'shimcha (yana bitta) filial yaratish
         (birinchi filialdan farqli — bu allaqachon filiali borlarga ham ochiq)
    """
    permission_classes = [IsAuthenticated, IsMerchantStaff]

    def get(self, request):
        profile = request.user.merchant_staff_profile
        branches = get_merchant_branches(profile.merchant_id)
        return Response({
            "branches": MerchantBranchSerializer(branches, many=True).data,
            "active_branch_id": str(profile.branch_id) if profile.branch_id else None,
        })

    def post(self, request):
        profile = request.user.merchant_staff_profile
        serializer = MerchantBranchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch = create_branch(profile.merchant, serializer.validated_data)
        if profile.branch is None:
            profile.branch = branch
            profile.save(update_fields=["branch"])
        return Response(MerchantBranchSerializer(branch).data, status=status.HTTP_201_CREATED)


class MyBranchDetailView(APIView):
    """PATCH /api/v1/merchant/branches/<branch_pk>/ — o'z filiallarimdan birini tahrirlash"""
    permission_classes = [IsAuthenticated, IsMerchantStaff]

    def patch(self, request, branch_pk):
        profile = request.user.merchant_staff_profile
        branch = get_branch_by_id(branch_pk, merchant_id=profile.merchant_id)
        if not branch:
            raise BranchNotFound()
        serializer = MerchantBranchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        branch = update_branch(branch.id, profile.merchant, serializer.validated_data)
        return Response(MerchantBranchSerializer(branch).data)


class MyBranchSwitchView(APIView):
    """
    POST /api/v1/merchant/branches/<branch_pk>/switch/

    Panel bir vaqtning o'zida bitta "faol" filial kontekstida ishlaydi
    (buyurtmalar, statistikalar shu filial bo'yicha). Bu — xodim qaysi
    filial nomidan ishlashini almashtirish uchun.
    """
    permission_classes = [IsAuthenticated, IsMerchantStaff]

    def post(self, request, branch_pk):
        profile = request.user.merchant_staff_profile
        branch = get_branch_by_id(branch_pk, merchant_id=profile.merchant_id)
        if not branch:
            raise BranchNotFound()
        profile.branch = branch
        profile.save(update_fields=["branch"])
        return Response(MerchantBranchSerializer(branch).data)


# ── Admin panel views ──────────────────────────────────────────────────────

class AdminPendingMerchantsView(APIView):
    """GET /api/v1/admin/merchants/pending/ — tasdiqlanishi kutilayotgan do'konlar"""
    permission_classes = [IsAuthenticated, IsAdminOrSupport]

    def get(self, request):
        merchants = get_pending_merchants()
        return Response(MerchantDetailSerializer(merchants, many=True).data)


class AdminMerchantApproveView(APIView):
    """POST /api/v1/admin/merchants/<pk>/approve/"""
    permission_classes = [IsAuthenticated, IsAdminOrSupport]

    def post(self, request, pk):
        merchant = Merchant.objects.filter(pk=pk).first()
        if not merchant:
            raise MerchantNotFound()
        merchant = approve_merchant(merchant)
        return Response(MerchantDetailSerializer(merchant).data)


class AdminMerchantRejectView(APIView):
    """POST /api/v1/admin/merchants/<pk>/reject/"""
    permission_classes = [IsAuthenticated, IsAdminOrSupport]

    def post(self, request, pk):
        merchant = Merchant.objects.filter(pk=pk).first()
        if not merchant:
            raise MerchantNotFound()
        merchant = reject_merchant(merchant)
        return Response(MerchantDetailSerializer(merchant).data)


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
