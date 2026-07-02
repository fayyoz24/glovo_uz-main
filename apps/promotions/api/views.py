"""
Promotions API Views.

Endpoints:
  Customer:
    POST   /api/v1/promotions/validate/         – promo kodni tekshirish
    GET    /api/v1/promotions/referral/          – o'z referal kodini ko'rish

  Admin:
    GET    /api/v1/admin/promotions/             – kampaniyalar ro'yxati
    POST   /api/v1/admin/promotions/             – yangi kampaniya
    GET    /api/v1/admin/promotions/{id}/        – kampaniya detail
    PATCH  /api/v1/admin/promotions/{id}/        – kampaniyani tahrirlash
    POST   /api/v1/admin/promotions/{id}/pause/  – to'xtatish
    POST   /api/v1/admin/promotions/{id}/activate/ – faollashtirish
    GET    /api/v1/admin/promotions/{id}/usages/ – foydalanish tarixi
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.promotions.api.serializers import (
    PromoCampaignCreateSerializer,
    PromoCampaignDetailSerializer,
    PromoCampaignListSerializer,
    PromoCampaignUpdateSerializer,
    PromoDiscountResponseSerializer,
    PromoUsageSerializer,
    PromoValidateSerializer,
    ReferralCodeSerializer,
)
from apps.promotions.exceptions import PromoError
from apps.promotions.permissions import IsAdminOrOps
from apps.promotions.selectors import (
    get_promo_by_id,
    get_promo_usages,
    get_promos_for_admin,
    get_referral_stats,
)
from apps.promotions.services import PromoService, ReferralService


# ═════════════════════════ CUSTOMER VIEWS ════════════════════════════════════


class PromoValidateView(APIView):
    """
    POST /api/v1/promotions/validate/

    Cart'da promo kodni tekshiradi va chegirma miqdorini qaytaradi.
    Aslida apply-promo cart service'da amalga oshiriladi,
    bu endpoint faqat preview uchun.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PromoValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            promo = PromoService.validate_promo(
                code=data["code"],
                user=request.user,
                subtotal=data["subtotal"],
                merchant_id=data.get("merchant_id"),
            )
        except PromoError as e:
            return Response(
                {"detail": e.message, "code": e.code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Chegirma hisoblash
        discount_info = PromoService.calculate_discount(
            promo=promo,
            subtotal=data["subtotal"],
        )

        response_data = {
            "code": promo.code,
            "discount_type": promo.discount_type,
            "discount_value": promo.discount_value,
            **discount_info,
            "message": "Promo kod muvaffaqiyatli qo'llandi!",
        }
        return Response(
            PromoDiscountResponseSerializer(response_data).data,
            status=status.HTTP_200_OK,
        )


class MyReferralCodeView(APIView):
    """
    GET /api/v1/promotions/referral/

    Foydalanuvchining o'z referal kodini ko'rish yoki yaratish.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        referral_code = ReferralService.get_or_create_referral_code(request.user)
        stats = get_referral_stats(request.user.id)

        return Response(
            {
                **ReferralCodeSerializer(referral_code).data,
                **stats,
            },
            status=status.HTTP_200_OK,
        )


# ═════════════════════════ ADMIN VIEWS ═══════════════════════════════════════


class AdminPromoCampaignListCreateView(APIView):
    """
    GET  /api/v1/admin/promotions/   – filtrlab ro'yxat
    POST /api/v1/admin/promotions/   – yangi kampaniya yaratish
    """

    permission_classes = [IsAuthenticated, IsAdminOrOps]

    def get(self, request):
        status_filter = request.query_params.get("status")
        search = request.query_params.get("search")
        qs = get_promos_for_admin(status=status_filter, search=search)
        serializer = PromoCampaignListSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PromoCampaignCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        promo = PromoService.create_campaign(
            created_by=request.user,
            **serializer.validated_data,
        )
        return Response(
            PromoCampaignDetailSerializer(promo).data,
            status=status.HTTP_201_CREATED,
        )


class AdminPromoCampaignDetailView(APIView):
    """
    GET   /api/v1/admin/promotions/{id}/
    PATCH /api/v1/admin/promotions/{id}/
    """

    permission_classes = [IsAuthenticated, IsAdminOrOps]

    def _get_promo_or_404(self, promo_id):
        promo = get_promo_by_id(promo_id)
        if promo is None:
            return None
        return promo

    def get(self, request, promo_id):
        promo = self._get_promo_or_404(promo_id)
        if promo is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        return Response(PromoCampaignDetailSerializer(promo).data)

    def patch(self, request, promo_id):
        promo = self._get_promo_or_404(promo_id)
        if promo is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PromoCampaignUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        promo = PromoService.update_campaign(promo, **serializer.validated_data)
        return Response(PromoCampaignDetailSerializer(promo).data)


class AdminPromoPauseView(APIView):
    """POST /api/v1/admin/promotions/{id}/pause/"""

    permission_classes = [IsAuthenticated, IsAdminOrOps]

    def post(self, request, promo_id):
        promo = get_promo_by_id(promo_id)
        if promo is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        promo = PromoService.pause_campaign(promo)
        return Response({"status": promo.status}, status=status.HTTP_200_OK)


class AdminPromoActivateView(APIView):
    """POST /api/v1/admin/promotions/{id}/activate/"""

    permission_classes = [IsAuthenticated, IsAdminOrOps]

    def post(self, request, promo_id):
        promo = get_promo_by_id(promo_id)
        if promo is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        promo = PromoService.activate_campaign(promo)
        return Response({"status": promo.status}, status=status.HTTP_200_OK)


class AdminPromoUsagesView(APIView):
    """GET /api/v1/admin/promotions/{id}/usages/"""

    permission_classes = [IsAuthenticated, IsAdminOrOps]

    def get(self, request, promo_id):
        promo = get_promo_by_id(promo_id)
        if promo is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        usages = get_promo_usages(promo_id=promo_id)
        serializer = PromoUsageSerializer(usages, many=True)
        return Response(serializer.data)
