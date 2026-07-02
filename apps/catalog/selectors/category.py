from apps.catalog.models import ProductCategory


def get_active_categories(parent_id=None):
    qs = ProductCategory.objects.filter(is_active=True)
    if parent_id is not None:
        qs = qs.filter(parent_id=parent_id)
    else:
        qs = qs.filter(parent__isnull=True)  # top-level only by default
    return qs.prefetch_related("children")


def get_category_by_id(category_id) -> ProductCategory | None:
    return ProductCategory.objects.filter(id=category_id, is_active=True).first()
