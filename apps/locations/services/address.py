from django.db import transaction
from apps.locations.models import Address
from apps.locations.selectors import get_address_by_id, get_user_address_or_404
from apps.locations.exceptions import AddressNotFound, AddressLimitExceeded

ADDRESS_LIMIT_PER_USER = 10


DEFAULT_CITY = "Qarshi"

# apps/locations/services.py

def create_address(user, validated_data: dict) -> Address:
    validated_data.pop("city", None)  # xavfsizlik uchun, model default'i o'zi ishlaydi
    address = Address.objects.create(user=user, **validated_data)
    return address


def update_address(user, pk, validated_data: dict) -> Address:
    validated_data.pop("city", None)
    address = get_user_address_or_404(user, pk)
    for field, value in validated_data.items():
        setattr(address, field, value)
    address.save()
    return address


def delete_address(user, address_id) -> None:
    address = get_address_by_id(address_id, user=user)
    if not address:
        raise AddressNotFound()
    address.delete()


def set_default_address(user, address_id) -> Address:
    address = get_address_by_id(address_id, user=user)
    if not address:
        raise AddressNotFound()
    with transaction.atomic():
        Address.objects.filter(user=user, is_default=True).update(is_default=False)
        address.is_default = True
        address.save(update_fields=["is_default"])
    return address
