"""
Reviews services – barcha biznes logika.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.reviews.constants import ReviewStatus
from apps.reviews.exceptions import (
    ReviewAlreadyExists,
    ReviewAlreadyReplied,
    ReviewNotAllowed,
    ReviewNotFound,
    ReviewNotOwner,
)
from apps.reviews.models import Review, ReviewFlag, ReviewImage
from apps.reviews.selectors import (
    get_review_by_id,
    get_review_by_order,
    has_review_for_order,
    has_user_flagged,
)


class ReviewService:

    # ─────────────────────── Yaratish ────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_review(
        *,
        order,
        customer,
        merchant_rating: int,
        merchant_comment: str = "",
        courier_rating: int | None = None,
        courier_comment: str = "",
        images: list | None = None,
    ) -> Review:
        """
        Faqat yetkazilgan (delivered) buyurtma uchun review yozish mumkin.
        Har bir buyurtma uchun faqat bitta review.
        """
        # Faqat delivered buyurtma baholanadi
        if order.status != "delivered":
            raise ReviewNotAllowed()

        # Allaqachon review bormi
        if has_review_for_order(order.id, customer.id):
            raise ReviewAlreadyExists()

        review = Review.objects.create(
            order=order,
            customer=customer,
            merchant=order.branch.merchant,
            merchant_rating=merchant_rating,
            merchant_comment=merchant_comment,
            courier=order.courier,
            courier_rating=courier_rating,
            courier_comment=courier_comment,
            status=ReviewStatus.VISIBLE,
        )

        # Rasmlar
        if images:
            ReviewService._attach_images(review, images)

        # Merchant va courier ratinglarini yangilaymiz
        ReviewService._update_merchant_rating(review.merchant_id)
        if review.courier_id:
            ReviewService._update_courier_rating(review.courier_id)

        return review

    @staticmethod
    def _attach_images(review: Review, images: list):
        """ImageField FileObject'larini saqlaydi."""
        for i, img in enumerate(images[:5]):  # Maksimal 5 ta rasm
            ReviewImage.objects.create(review=review, image=img, sort_order=i)

    # ─────────────────────── Tahrirlash ──────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def update_review(
        *,
        review: Review,
        customer,
        merchant_rating: int | None = None,
        merchant_comment: str | None = None,
        courier_rating: int | None = None,
        courier_comment: str | None = None,
    ) -> Review:
        """Mijoz o'z reviewini o'zgartirishi mumkin (faqat 24 soat ichida)."""
        if review.customer_id != customer.id:
            raise ReviewNotOwner()

        # 24 soatlik muddatni tekshirish
        from datetime import timedelta
        if timezone.now() - review.created_at > timedelta(hours=24):
            raise ReviewNotAllowed()

        if merchant_rating is not None:
            review.merchant_rating = merchant_rating
        if merchant_comment is not None:
            review.merchant_comment = merchant_comment
        if courier_rating is not None:
            review.courier_rating = courier_rating
        if courier_comment is not None:
            review.courier_comment = courier_comment

        review.save(
            update_fields=[
                "merchant_rating",
                "merchant_comment",
                "courier_rating",
                "courier_comment",
                "updated_at",
            ]
        )

        ReviewService._update_merchant_rating(review.merchant_id)
        if review.courier_id:
            ReviewService._update_courier_rating(review.courier_id)

        return review

    # ─────────────────────── Merchant javobi ─────────────────────────────────

    @staticmethod
    def add_merchant_reply(*, review: Review, reply_text: str) -> Review:
        """Merchant o'z do'koniga yozilgan reviewga javob beradi."""
        if review.merchant_reply:
            raise ReviewAlreadyReplied()

        review.merchant_reply = reply_text
        review.merchant_replied_at = timezone.now()
        review.save(update_fields=["merchant_reply", "merchant_replied_at", "updated_at"])
        return review

    # ─────────────────────── Shikoyat ────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def flag_review(*, review: Review, user, reason: str, note: str = "") -> ReviewFlag:
        """Foydalanuvchi reviewni shikoyat qiladi."""
        if has_user_flagged(user.id, review.id):
            from reviews.exceptions import ReviewError
            raise ReviewError("Siz bu reviewni allaqachon shikoyat qilgansiz.", "already_flagged")

        flag = ReviewFlag.objects.create(
            review=review,
            flagged_by=user,
            reason=reason,
            note=note,
        )

        from django.db.models import F
        Review.objects.filter(pk=review.pk).update(flag_count=F("flag_count") + 1)

        # 3 va undan ko'p shikoyat bo'lsa avtomatik FLAGGED holatiga o'tkazish
        review.refresh_from_db(fields=["flag_count"])
        if review.flag_count >= 3:
            Review.objects.filter(pk=review.pk).update(status=ReviewStatus.FLAGGED)

        return flag

    # ─────────────────────── Admin moderatsiya ────────────────────────────────

    @staticmethod
    def hide_review(*, review: Review, admin_user, note: str = "") -> Review:
        review.status = ReviewStatus.HIDDEN
        review.admin_note = note
        review.moderated_by = admin_user
        review.moderated_at = timezone.now()
        review.save(
            update_fields=["status", "admin_note", "moderated_by", "moderated_at", "updated_at"]
        )
        ReviewService._update_merchant_rating(review.merchant_id)
        if review.courier_id:
            ReviewService._update_courier_rating(review.courier_id)
        return review

    @staticmethod
    def restore_review(*, review: Review, admin_user, note: str = "") -> Review:
        review.status = ReviewStatus.VISIBLE
        review.flag_count = 0
        review.admin_note = note
        review.moderated_by = admin_user
        review.moderated_at = timezone.now()
        review.save(
            update_fields=[
                "status", "flag_count", "admin_note",
                "moderated_by", "moderated_at", "updated_at",
            ]
        )
        ReviewService._update_merchant_rating(review.merchant_id)
        if review.courier_id:
            ReviewService._update_courier_rating(review.courier_id)
        return review

    # ─────────────────────── Rating yangilash ────────────────────────────────

    @staticmethod
    def _update_merchant_rating(merchant_id):
        """
        Merchant.rating_avg ni qayta hisoblaydi.
        Merchant modeli avg_rating maydoniga ega bo'lishi kerak.
        """
        from django.db.models import Avg
        from merchants.models import Merchant  # lazy import

        avg = (
            Review.objects.filter(
                merchant_id=merchant_id,
                status=ReviewStatus.VISIBLE,
            ).aggregate(avg=Avg("merchant_rating"))["avg"]
            or 0
        )
        Merchant.objects.filter(pk=merchant_id).update(rating_avg=round(avg, 2))

    @staticmethod
    def _update_courier_rating(courier_id):
        """
        CourierProfile.rating ni qayta hisoblaydi.
        """
        from django.db.models import Avg
        from accounts.models import CourierProfile  # lazy import

        avg = (
            Review.objects.filter(
                courier_id=courier_id,
                status=ReviewStatus.VISIBLE,
                courier_rating__isnull=False,
            ).aggregate(avg=Avg("courier_rating"))["avg"]
            or 0
        )
        CourierProfile.objects.filter(user_id=courier_id).update(rating=round(avg, 2))
