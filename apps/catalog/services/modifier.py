from apps.catalog.models import ProductModifierGroup, ProductModifierOption
from apps.catalog.exceptions import InvalidModifier, ModifierSelectionError


def validate_modifier_selection(product, selected_modifier_option_ids: list[str]) -> list[ProductModifierOption]:
    """
    Validates that selected modifier options:
    1. Belong to this product's groups
    2. Satisfy min_select / max_select per group
    3. All options are active
    Returns list of resolved ProductModifierOption objects.
    """
    groups = ProductModifierGroup.objects.filter(
        product=product, is_active=True
    ).prefetch_related("options")

    selected_ids = set(str(oid) for oid in selected_modifier_option_ids)
    resolved_options = []

    for group in groups:
        group_option_ids = {str(opt.id) for opt in group.options.filter(is_active=True)}
        chosen = selected_ids & group_option_ids

        if len(chosen) < group.min_select:
            raise ModifierSelectionError(
                detail=f"'{group.name_ru}' guruhidan kamida {group.min_select} ta tanlang."
            )
        if len(chosen) > group.max_select:
            raise ModifierSelectionError(
                detail=f"'{group.name_ru}' guruhidan ko'pi bilan {group.max_select} ta tanlash mumkin."
            )

        for opt in group.options.filter(is_active=True):
            if str(opt.id) in chosen:
                resolved_options.append(opt)

    # Check for any selected IDs not belonging to this product
    all_valid_ids = set()
    for group in groups:
        for opt in group.options.all():
            all_valid_ids.add(str(opt.id))

    unknown = selected_ids - all_valid_ids
    if unknown:
        raise InvalidModifier(detail=f"Noto'g'ri modifier tanlov: {unknown}")

    return resolved_options
