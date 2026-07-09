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


def get_merchants_owned_by(owner) -> "list[Merchant]":
    """Foydalanuvchi topshirgan barcha do'kon arizalari (holatidan qat'i nazar)."""
    return list(Merchant.objects.filter(owner=owner).order_by("-created_at"))


def count_pending_merchants_for_owner(owner) -> int:
    return Merchant.objects.filter(owner=owner, status=MerchantStatus.PENDING).count()


def get_pending_merchants() -> "list[Merchant]":
    """Admin panel uchun — tasdiqlanishi kerak bo'lgan do'konlar."""
    return list(Merchant.objects.filter(status=MerchantStatus.PENDING).order_by("created_at"))
