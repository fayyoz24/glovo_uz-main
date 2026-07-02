from apps.locations.models import Address


def get_user_addresses(user):
    return Address.objects.filter(user=user).order_by("-is_default", "-created_at")


def get_address_by_id(address_id, user=None):
    qs = Address.objects.filter(id=address_id)
    if user:
        qs = qs.filter(user=user)
    return qs.first()
