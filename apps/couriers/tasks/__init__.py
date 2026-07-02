try:
    from celery import shared_task
except ImportError:
    def shared_task(func):
        return func


@shared_task
def cleanup_old_location_pings():
    """
    7 kundan eski location ping yozuvlarini o'chiradi.
    Celery Beat: har kecha soat 02:00 da ishlaydi.
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.couriers.models import CourierLocationPing

    cutoff = timezone.now() - timedelta(days=7)
    deleted, _ = CourierLocationPing.objects.filter(recorded_at__lt=cutoff).delete()
    print(f"[TASK] Deleted {deleted} old location pings")
    return deleted


@shared_task
def auto_end_stale_shifts():
    """
    12 soatdan uzun davom etgan smenalarni avtomatik yopadi.
    Celery Beat: har soatda ishlaydi.
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.couriers.models import CourierShift
    from apps.couriers.constants import ShiftStatus, CourierStatus
    from apps.couriers.models import CourierProfile

    cutoff = timezone.now() - timedelta(hours=12)
    stale_shifts = CourierShift.objects.filter(
        status=ShiftStatus.ACTIVE,
        start_time__lt=cutoff,
    )
    count = 0
    for shift in stale_shifts:
        shift.status = ShiftStatus.ENDED
        shift.end_time = timezone.now()
        shift.save()
        CourierProfile.objects.filter(user=shift.courier).update(
            courier_status=CourierStatus.OFFLINE
        )
        count += 1
    print(f"[TASK] Auto-ended {count} stale shifts")
    return count
