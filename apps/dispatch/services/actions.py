"""
Kuryer tomonidan buyurtma taklifiga javob berish: qabul / rad etish.
"""
from django.db import transaction
from django.utils import timezone

from apps.dispatch.models import CourierAssignment
from apps.dispatch.constants import AssignmentStatus
from apps.dispatch.selectors import get_assignment_for_courier
from apps.dispatch.exceptions import AssignmentAlreadyActioned, AssignmentNotFound
from apps.orders.constants import OrderStatus
from apps.orders.services import transition_order_status
from apps.couriers.services import set_courier_busy


@transaction.atomic
def courier_accept_order(*, courier_user, assignment_id) -> CourierAssignment:
    assignment = get_assignment_for_courier(assignment_id, courier_user)

    if assignment.status != AssignmentStatus.OFFERED:
        raise AssignmentAlreadyActioned()

    if assignment.is_expired:
        assignment.status = AssignmentStatus.TIMED_OUT
        assignment.save()
        raise AssignmentAlreadyActioned(detail="Taklif vaqti tugagan.")

    assignment.status = AssignmentStatus.ACCEPTED
    assignment.accepted_at = timezone.now()
    assignment.save()

    # Buyurtma statusini yangilash va kuryerni biriktirish
    order = assignment.order
    order.courier = courier_user
    order.save(update_fields=["courier", "updated_at"])

    transition_order_status(
        order=order,
        to_status=OrderStatus.COURIER_ASSIGNED,
        changed_by=courier_user,
        note=f"Kuryer #{courier_user.id} qabul qildi",
    )

    # Kuryerni BUSY ga o'tkazish
    set_courier_busy(courier_user=courier_user)

    return assignment


@transaction.atomic
def courier_reject_order(*, courier_user, assignment_id) -> CourierAssignment:
    assignment = get_assignment_for_courier(assignment_id, courier_user)

    if assignment.status != AssignmentStatus.OFFERED:
        raise AssignmentAlreadyActioned()

    assignment.status = AssignmentStatus.REJECTED
    assignment.rejected_at = timezone.now()
    assignment.save()

    # Boshqa kuryer qidirish
    try:
        from apps.dispatch.services.assign import reassign_or_escalate
        reassign_or_escalate(assignment.order)
    except Exception as e:
        print(f"[DISPATCH] Reassign error: {e}")

    return assignment
