from django.db.models import Q
from apps.catalog.models import Product


def _base_available_qs():
    return (
        Product.objects.filter(is_active=True, is_available=True, status="active")
        .select_related("category")
        .prefetch_related("images", "variants", "modifier_groups__options")
    )


def get_products_for_branch(branch_id):
    """Products belonging to a specific branch OR shared across all branches (branch=null)."""
    return _base_available_qs().filter(
        Q(branch_id=branch_id) | Q(branch__isnull=True)
    )


def get_products_for_merchant(merchant_id, category_id=None):
    qs = _base_available_qs().filter(merchant_id=merchant_id)
    if category_id:
        qs = qs.filter(category_id=category_id)
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
