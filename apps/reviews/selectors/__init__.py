"""
Reviews selectors – faqat READ operatsiyalari.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from django.db.models import Avg, Count, Q, QuerySet

from apps.reviews.constants import ReviewStatus
from apps.reviews.models import Review, ReviewFlag


# ──────────────────────────── Review ─────────────────────────────────────────


def get_review_by_id(review_id: UUID) -> Optional[Review]:
    try:
        return Review.objects.select_related(
            "customer", "merchant", "courier", "order"
        ).get(id=review_id)
    except Review.DoesNotExist:
        return None


def get_review_by_order(order_id) -> Optional[Review]:
    try:
        return Review.objects.get(order_id=order_id)
    except Review.DoesNotExist:
        return None


def has_review_for_order(order_id, customer_id) -> bool:
    return Review.objects.filter(order_id=order_id, customer_id=customer_id).exists()


def get_merchant_reviews(
    merchant_id,
    status: str = ReviewStatus.VISIBLE,
    rating: Optional[int] = None,
) -> QuerySet[Review]:
    qs = Review.objects.filter(
        merchant_id=merchant_id,
        status=status,
    ).select_related("customer", "order").prefetch_related("images")

    if rating:
        qs = qs.filter(merchant_rating=rating)

    return qs.order_by("-created_at")


def get_courier_reviews(
    courier_id,
    status: str = ReviewStatus.VISIBLE,
) -> QuerySet[Review]:
    return (
        Review.objects.filter(
            courier_id=courier_id,
            status=status,
            courier_rating__isnull=False,
        )
        .select_related("customer", "order")
        .order_by("-created_at")
    )


def get_customer_reviews(customer_id) -> QuerySet[Review]:
    return (
        Review.objects.filter(customer_id=customer_id)
        .select_related("merchant", "order")
        .prefetch_related("images")
        .order_by("-created_at")
    )


def get_merchant_rating_stats(merchant_id) -> dict:
    """
    Do'konning reyting statistikasi.
    Returns: {avg_rating, total_count, distribution: {1:N, 2:N, ...}}
    """
    qs = Review.objects.filter(
        merchant_id=merchant_id,
        status=ReviewStatus.VISIBLE,
    )
    agg = qs.aggregate(
        avg=Avg("merchant_rating"),
        total=Count("id"),
    )
    distribution = {
        i: qs.filter(merchant_rating=i).count() for i in range(1, 6)
    }
    return {
        "avg_rating": round(agg["avg"] or 0, 2),
        "total_count": agg["total"],
        "distribution": distribution,
    }


def get_courier_rating_stats(courier_id) -> dict:
    qs = Review.objects.filter(
        courier_id=courier_id,
        status=ReviewStatus.VISIBLE,
        courier_rating__isnull=False,
    )
    agg = qs.aggregate(avg=Avg("courier_rating"), total=Count("id"))
    return {
        "avg_rating": round(agg["avg"] or 0, 2),
        "total_count": agg["total"],
    }


# ──────────────────────────── Admin ──────────────────────────────────────────


def get_reviews_for_admin(
    status: Optional[str] = None,
    merchant_id=None,
    flagged_only: bool = False,
    search: Optional[str] = None,
) -> QuerySet[Review]:
    qs = Review.objects.select_related(
        "customer", "merchant", "courier", "order"
    ).order_by("-created_at")

    if status:
        qs = qs.filter(status=status)
    if merchant_id:
        qs = qs.filter(merchant_id=merchant_id)
    if flagged_only:
        qs = qs.filter(status=ReviewStatus.FLAGGED)
    if search:
        qs = qs.filter(
            Q(merchant_comment__icontains=search)
            | Q(courier_comment__icontains=search)
            | Q(customer__phone__icontains=search)
        )
    return qs


def get_pending_reviews() -> QuerySet[Review]:
    return Review.objects.filter(status=ReviewStatus.PENDING).order_by("created_at")


# ──────────────────────────── ReviewFlag ─────────────────────────────────────


def get_flag_by_user_and_review(user_id, review_id) -> Optional[ReviewFlag]:
    try:
        return ReviewFlag.objects.get(review_id=review_id, flagged_by_id=user_id)
    except ReviewFlag.DoesNotExist:
        return None


def has_user_flagged(user_id, review_id) -> bool:
    return ReviewFlag.objects.filter(
        review_id=review_id, flagged_by_id=user_id
    ).exists()
