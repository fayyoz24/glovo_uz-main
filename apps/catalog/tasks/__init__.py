from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(name="apps.catalog.tasks.sync_product_availability", bind=True, max_retries=3)
def sync_product_availability(self):
    """
    Branchlarning `is_open` statusiga qarab productlarning
    `is_available` flagini sinxronlashtiradi.
    Har 15 daqiqada ishga tushadi.
    """
    try:
        from apps.catalog.models import Product
        from apps.catalog.constants import ProductStatus

        # Yopiq branchlarga tegishli productlarni temporarily unavailable qilish
        closed_branch_ids = list(
            __import__("apps.merchants.models", fromlist=["MerchantBranch"])
            .MerchantBranch.objects.filter(is_open=False)
            .values_list("id", flat=True)
        )

        made_unavailable = Product.objects.filter(
            branch_id__in=closed_branch_ids,
            is_available=True,
            status=ProductStatus.ACTIVE,
        ).update(is_available=False)

        # Ochiq branchlarga tegishli productlarni qaytarish
        open_branch_ids = list(
            __import__("apps.merchants.models", fromlist=["MerchantBranch"])
            .MerchantBranch.objects.filter(is_open=True, accepting_orders=True)
            .values_list("id", flat=True)
        )

        made_available = Product.objects.filter(
            branch_id__in=open_branch_ids,
            is_available=False,
            status=ProductStatus.ACTIVE,
        ).update(is_available=True)

        logger.info(
            f"[Product Sync] {made_unavailable} ta unavailable, "
            f"{made_available} ta available qilindi."
        )
        return {"made_unavailable": made_unavailable, "made_available": made_available}
    except Exception as exc:
        logger.error(f"[Product Sync] Xatolik: {exc}")
        raise self.retry(exc=exc, countdown=60)
