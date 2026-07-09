from django.db.models import Q
from apps.catalog.models import ProductCategory


def get_active_categories(parent_id=None, merchant_type_code=None):
    qs = ProductCategory.objects.filter(is_active=True)
    if parent_id is not None:
        qs = qs.filter(parent_id=parent_id)
    else:
        qs = qs.filter(parent__isnull=True)  # top-level only by default
    if merchant_type_code:
        # Faqat shu do'kon turiga tegishli yoki hech qaysi turga bog'lanmagan
        # (umumiy) kategoriyalarni ko'rsatamiz.
        qs = qs.filter(Q(merchant_type__code=merchant_type_code) | Q(merchant_type__isnull=True))
    return qs.prefetch_related("children")


def get_category_by_id(category_id) -> ProductCategory | None:
    return ProductCategory.objects.filter(id=category_id, is_active=True).first()
