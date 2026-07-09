from django.db.models import Q
from apps.catalog.models import Product


def _base_available_qs():
    return (
        Product.objects.filter(is_active=True, is_available=True, status="active")
        .select_related("category")
        .prefetch_related("images", "variants", "modifier_groups__options")
    )


def get_products_for_branch(branch_id, category_id=None, search=""):
    """Products belonging to a specific branch OR shared across all branches (branch=null)."""
    qs = _base_available_qs().filter(
        Q(branch_id=branch_id) | Q(branch__isnull=True)
    )
    if category_id:
        qs = qs.filter(category_id=category_id)
    if search:
        qs = qs.filter(
            Q(name_ru__icontains=search)
            | Q(name_uz__icontains=search)
            | Q(description_ru__icontains=search)
        )
    return qs


def get_products_for_merchant(merchant_id, category_id=None, search=""):
    """
    Merchant panel uchun — do'konning BARCHA mahsulotlari (holatidan qat'i
    nazar: nofaol/tugagan bo'lsa ham), chunki xodim ularni shu yerdan
    boshqaradi (narx, mavjudlik va h.k.).
    """
    qs = (
        Product.objects.filter(merchant_id=merchant_id)
        .select_related("category")
        .prefetch_related("images", "variants", "modifier_groups__options")
        .order_by("sort_order", "name_ru")
    )
    if category_id:
        qs = qs.filter(category_id=category_id)
    if search:
        qs = qs.filter(
            Q(name_ru__icontains=search)
            | Q(name_uz__icontains=search)
            | Q(description_ru__icontains=search)
        )
    return qs


def get_product_by_id(product_id) -> Product | None:
    try:
        return _base_available_qs().get(id=product_id)
    except Product.DoesNotExist:
        return None


def search_products(query: str, merchant_id=None):
    qs = _base_available_qs().filter(
        Q(name_ru__icontains=query)
        | Q(name_uz__icontains=query)
        | Q(description_ru__icontains=query)
    )
    if merchant_id:
        qs = qs.filter(merchant_id=merchant_id)
    return qs[:50]