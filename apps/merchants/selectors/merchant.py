from apps.merchants.models import Merchant
from apps.merchants.constants import MerchantStatus


def get_active_merchants(merchant_type: str | None = None):
    qs = Merchant.objects.filter(status=MerchantStatus.ACTIVE)
    if merchant_type:
        qs = qs.filter(type=merchant_type)
    return qs.order_by("-rating_avg")


def get_merchant_by_id(merchant_id) -> Merchant | None:
    return Merchant.objects.filter(id=merchant_id, status=MerchantStatus.ACTIVE).first()


def get_merchant_by_slug(slug: str) -> Merchant | None:
    return Merchant.objects.filter(slug=slug, status=MerchantStatus.ACTIVE).first()
