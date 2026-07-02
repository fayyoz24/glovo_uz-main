"""
Reviews Celery tasks.
"""
from celery import shared_task


@shared_task
def recalculate_merchant_ratings():
    """
    Barcha merchantlarning rating_avg ni qayta hisoblaydi.
    Har kuni ishga tushiriladi (Celery Beat).
    """
    from django.db.models import Avg

    from merchants.models import Merchant
    from reviews.constants import ReviewStatus
    from reviews.models import Review

    merchants = Merchant.objects.values_list("id", flat=True)
    updated = 0

    for merchant_id in merchants:
        avg = (
            Review.objects.filter(
                merchant_id=merchant_id,
                status=ReviewStatus.VISIBLE,
            ).aggregate(avg=Avg("merchant_rating"))["avg"]
            or 0
        )
        Merchant.objects.filter(pk=merchant_id).update(rating_avg=round(avg, 2))
        updated += 1

    return f"{updated} ta merchant reytingi yangilandi."


@shared_task
def recalculate_courier_ratings():
    """
    Barcha kuryerlarning ratingini qayta hisoblaydi.
    """
    from django.db.models import Avg

    from accounts.models import CourierProfile
    from reviews.constants import ReviewStatus
    from reviews.models import Review

    couriers = CourierProfile.objects.values_list("user_id", flat=True)
    updated = 0

    for courier_id in couriers:
        avg = (
            Review.objects.filter(
                courier_id=courier_id,
                status=ReviewStatus.VISIBLE,
                courier_rating__isnull=False,
            ).aggregate(avg=Avg("courier_rating"))["avg"]
            or 0
        )
        CourierProfile.objects.filter(user_id=courier_id).update(rating=round(avg, 2))
        updated += 1

    return f"{updated} ta kuryer reytingi yangilandi."


@shared_task
def notify_merchant_new_review(review_id: str):
    """
    Yangi review kelganda merchantga bildirishnoma yuboradi.
    Notifications app'i orqali.
    """
    try:
        from reviews.models import Review

        review = Review.objects.select_related("merchant", "order").get(id=review_id)

        # NotificationService.send_merchant_notification(
        #     merchant=review.merchant,
        #     event="new_review",
        #     data={"rating": review.merchant_rating, "order_id": str(review.order_id)},
        # )
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            "New review notification: merchant=%s, review=%s, rating=%s",
            review.merchant_id,
            review_id,
            review.merchant_rating,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("notify_merchant_new_review failed: %s", e)
