"""
Reviews API Views.

Endpoints:
  Customer:
    POST   /api/v1/orders/{order_id}/review/            – review yozish
    GET    /api/v1/reviews/{id}/                        – review detail
    PATCH  /api/v1/reviews/{id}/                        – tahrirlash (24 soat)
    POST   /api/v1/reviews/{id}/flag/                   – shikoyat

  Public (auth shart emas):
    GET    /api/v1/merchants/{merchant_id}/reviews/      – do'kon reviewlari
    GET    /api/v1/merchants/{merchant_id}/rating-stats/ – reyting statistikasi

  Merchant panel:
    GET    /api/v1/merchant/reviews/                    – o'z do'koniga kelgan reviewlar
    POST   /api/v1/merchant/reviews/{id}/reply/         – reviewga javob berish

  Admin:
    GET    /api/v1/admin/reviews/                       – barchasi (filter bilan)
    GET    /api/v1/admin/reviews/{id}/                  – detail
    POST   /api/v1/admin/reviews/{id}/hide/             – yashirish
    POST   /api/v1/admin/reviews/{id}/restore/          – tiklash
"""
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reviews.api.serializers import (
    AdminModerationSerializer,
    AdminReviewDetailSerializer,
    AdminReviewListSerializer,
    MerchantRatingStatsSerializer,
    MerchantReplySerializer,
    MerchantReviewListSerializer,
    ReviewCreateSerializer,
    ReviewDetailSerializer,
    ReviewFlagSerializer,
    ReviewUpdateSerializer,
)
from apps.reviews.exceptions import ReviewError
from apps.reviews.permissions import IsAdminOrOps, IsMerchantStaff, IsReviewOwner
from apps.reviews.selectors import (
    get_courier_rating_stats,
    get_courier_reviews,
    get_customer_reviews,
    get_merchant_rating_stats,
    get_merchant_reviews,
    get_review_by_id,
    get_reviews_for_admin,
)
from apps.reviews.services import ReviewService


def _get_order_or_404(order_id, customer):
    """orders.Order'ni topadi, yo'q bo'lsa None qaytaradi."""
    try:
        from orders.models import Order
        return Order.objects.select_related("branch__merchant", "courier").get(
            id=order_id, customer=customer
        )
    except Exception:
        return None


# ═════════════════════════ CUSTOMER ══════════════════════════════════════════


class OrderReviewCreateView(APIView):
    """
    POST /api/v1/orders/{order_id}/review/
    Buyurtma yetkazilgandan keyin review yozish.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = _get_order_or_404(order_id, request.user)
        if order is None:
            return Response({"detail": "Buyurtma topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            review = ReviewService.create_review(
                order=order,
                customer=request.user,
                merchant_rating=data["merchant_rating"],
                merchant_comment=data.get("merchant_comment", ""),
                courier_rating=data.get("courier_rating"),
                courier_comment=data.get("courier_comment", ""),
                images=data.get("images"),
            )
        except ReviewError as e:
            return Response({"detail": e.message, "code": e.code}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ReviewDetailSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewDetailUpdateView(APIView):
    """
    GET   /api/v1/reviews/{id}/   – detail
    PATCH /api/v1/reviews/{id}/   – tahrirlash (24 soat ichida)
    """

    permission_classes = [IsAuthenticated]

    def _get_review(self, review_id, user):
        review = get_review_by_id(review_id)
        if review is None or review.customer_id != user.id:
            return None
        return review

    def get(self, request, review_id):
        review = self._get_review(review_id, request.user)
        if review is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ReviewDetailSerializer(review).data)

    def patch(self, request, review_id):
        review = self._get_review(review_id, request.user)
        if review is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            review = ReviewService.update_review(
                review=review,
                customer=request.user,
                **serializer.validated_data,
            )
        except ReviewError as e:
            return Response({"detail": e.message, "code": e.code}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ReviewDetailSerializer(review).data)


class MyReviewsView(APIView):
    """GET /api/v1/reviews/my/ – mijozning barcha reviewlari."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        reviews = get_customer_reviews(request.user.id)
        return Response(ReviewDetailSerializer(reviews, many=True).data)


class ReviewFlagView(APIView):
    """POST /api/v1/reviews/{id}/flag/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        review = get_review_by_id(review_id)
        if review is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewFlagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ReviewService.flag_review(
                review=review,
                user=request.user,
                reason=serializer.validated_data["reason"],
                note=serializer.validated_data.get("note", ""),
            )
        except ReviewError as e:
            return Response({"detail": e.message, "code": e.code}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Shikoyat qabul qilindi."}, status=status.HTTP_200_OK)


# ═════════════════════════ PUBLIC ════════════════════════════════════════════


class MerchantReviewListView(APIView):
    """
    GET /api/v1/merchants/{merchant_id}/reviews/
    Do'kon sahifasida ko'rinadigan reviewlar (auth shart emas).
    """

    permission_classes = [AllowAny]

    def get(self, request, merchant_id):
        rating = request.query_params.get("rating")
        rating = int(rating) if rating and rating.isdigit() else None

        reviews = get_merchant_reviews(merchant_id=merchant_id, rating=rating)
        return Response(MerchantReviewListSerializer(reviews, many=True).data)


class MerchantRatingStatsView(APIView):
    """
    GET /api/v1/merchants/{merchant_id}/rating-stats/
    Reyting statistikasi (distribution ham bor).
    """

    permission_classes = [AllowAny]

    def get(self, request, merchant_id):
        stats = get_merchant_rating_stats(merchant_id)
        return Response(MerchantRatingStatsSerializer(stats).data)


# ═════════════════════════ MERCHANT PANEL ════════════════════════════════════


class MerchantPanelReviewListView(APIView):
    """
    GET /api/v1/merchant/reviews/
    Merchant o'z do'koniga kelgan reviewlarni ko'radi.
    """

    permission_classes = [IsAuthenticated, IsMerchantStaff]

    def get(self, request):
        # MerchantStaffProfile orqali merchant_id olish
        try:
            merchant_id = request.user.merchant_staff_profile.merchant_id
        except Exception:
            return Response({"detail": "Do'kon topilmadi."}, status=status.HTTP_403_FORBIDDEN)

        rating = request.query_params.get("rating")
        rating = int(rating) if rating and rating.isdigit() else None

        reviews = get_merchant_reviews(merchant_id=merchant_id, rating=rating)
        return Response(MerchantReviewListSerializer(reviews, many=True).data)


class MerchantReplyView(APIView):
    """
    POST /api/v1/merchant/reviews/{review_id}/reply/
    Merchant reviewga javob beradi.
    """

    permission_classes = [IsAuthenticated, IsMerchantStaff]

    def post(self, request, review_id):
        review = get_review_by_id(review_id)
        if review is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        # Faqat o'z do'konining reviewiga javob berishi mumkin
        try:
            merchant_id = request.user.merchant_staff_profile.merchant_id
        except Exception:
            return Response({"detail": "Ruxsat yo'q."}, status=status.HTTP_403_FORBIDDEN)

        if str(review.merchant_id) != str(merchant_id):
            return Response({"detail": "Bu review sizning do'koningizga tegishli emas."}, status=status.HTTP_403_FORBIDDEN)

        serializer = MerchantReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            review = ReviewService.add_merchant_reply(
                review=review,
                reply_text=serializer.validated_data["reply_text"],
            )
        except ReviewError as e:
            return Response({"detail": e.message, "code": e.code}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ReviewDetailSerializer(review).data)


# ═════════════════════════ ADMIN ═════════════════════════════════════════════


class AdminReviewListView(APIView):
    """GET /api/v1/admin/reviews/"""

    permission_classes = [IsAuthenticated, IsAdminOrOps]

    def get(self, request):
        status_filter = request.query_params.get("status")
        merchant_id = request.query_params.get("merchant_id")
        flagged_only = request.query_params.get("flagged") == "true"
        search = request.query_params.get("search")

        reviews = get_reviews_for_admin(
            status=status_filter,
            merchant_id=merchant_id,
            flagged_only=flagged_only,
            search=search,
        )
        return Response(AdminReviewListSerializer(reviews, many=True).data)


class AdminReviewDetailView(APIView):
    """GET /api/v1/admin/reviews/{id}/"""

    permission_classes = [IsAuthenticated, IsAdminOrOps]

    def get(self, request, review_id):
        review = get_review_by_id(review_id)
        if review is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminReviewDetailSerializer(review).data)


class AdminReviewHideView(APIView):
    """POST /api/v1/admin/reviews/{id}/hide/"""

    permission_classes = [IsAuthenticated, IsAdminOrOps]

    def post(self, request, review_id):
        review = get_review_by_id(review_id)
        if review is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminModerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = ReviewService.hide_review(
            review=review,
            admin_user=request.user,
            note=serializer.validated_data.get("note", ""),
        )
        return Response({"status": review.status}, status=status.HTTP_200_OK)


class AdminReviewRestoreView(APIView):
    """POST /api/v1/admin/reviews/{id}/restore/"""

    permission_classes = [IsAuthenticated, IsAdminOrOps]

    def post(self, request, review_id):
        review = get_review_by_id(review_id)
        if review is None:
            return Response({"detail": "Topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminModerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = ReviewService.restore_review(
            review=review,
            admin_user=request.user,
            note=serializer.validated_data.get("note", ""),
        )
        return Response({"status": review.status}, status=status.HTTP_200_OK)
