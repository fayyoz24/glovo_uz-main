from apps.locations.models import Address
from django.shortcuts import get_object_or_404

def get_user_addresses(user):
    return Address.objects.filter(user=user).order_by("-is_default", "-created_at")


def get_user_address_or_404(user, pk) -> Address:
    return get_object_or_404(Address, pk=pk, user=user)


def get_address_by_id(address_id, user=None):
    qs = Address.objects.filter(id=address_id)
    if user:
        qs = qs.filter(user=user)
    return qs.first()
