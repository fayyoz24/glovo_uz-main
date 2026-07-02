from apps.merchants.models import MerchantBranch
from apps.common.utils import haversine_distance


def get_merchant_branches(merchant_id):
    return MerchantBranch.objects.filter(merchant_id=merchant_id).order_by("name")


def get_branch_by_id(branch_id, merchant_id=None) -> MerchantBranch | None:
    qs = MerchantBranch.objects.filter(id=branch_id)
    if merchant_id:
        qs = qs.filter(merchant_id=merchant_id)
    return qs.first()


def get_nearby_branches(lat: float, lng: float, radius_km: float = 5.0):
    """
    Return branches whose service radius covers the given coordinates.
    For MVP: Python-level filtering. Phase 2: move to PostGIS ST_DWithin.
    """
    branches = MerchantBranch.objects.filter(
        is_open=True,
        accepting_orders=True,
        merchant__status="active",
        latitude__isnull=False,
    ).select_related("merchant")

    result = []
    for branch in branches:
        dist = haversine_distance(lat, lng, float(branch.latitude), float(branch.longitude))
        if dist <= float(branch.service_radius_km):
            result.append((dist, branch))

    result.sort(key=lambda x: x[0])
    return [branch for _, branch in result]
