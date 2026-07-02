from apps.locations.models import ServiceZone
from apps.common.utils import haversine_distance


def get_active_zones(city: str | None = None):
    qs = ServiceZone.objects.filter(is_active=True)
    if city:
        qs = qs.filter(city=city)
    return qs


def get_zone_for_coordinates(lat: float, lng: float) -> ServiceZone | None:
    """Find the first active service zone that contains the given coordinates."""
    zones = ServiceZone.objects.filter(is_active=True, center_lat__isnull=False)
    for zone in zones:
        distance = haversine_distance(
            lat, lng,
            float(zone.center_lat), float(zone.center_lng),
        )
        if distance <= float(zone.radius_km):
            return zone
    return None
